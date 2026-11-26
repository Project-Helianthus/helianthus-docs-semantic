// Command resolve reports, from Go's own name resolution, which declared
// symbols of a donor module each declaration, test function and assertion
// uses.
//
// It reads one JSON document on standard input and writes one on standard
// output. The input holds the module path of the donor, the text of every Go
// file of the donor at the commit (keyed by repository-relative path) and the
// donor directories the move names. Every name is resolved by go/types: a
// field label, a parameter, a receiver, a local binding, a type parameter, a
// label and a package name is never a symbol, and a method, a method
// expression, a composite literal, a type switch case and a generic
// instantiation resolve as the language resolves them.
//
// The program uses the standard library only. A donor package is checked from
// the files the commit holds, for the platform linux/amd64 without cgo; the
// standard library is read from its source; a package that is neither of the
// two is replaced by an empty package of its name. Unresolved receiver
// selectors are reported separately from resolved donor references.
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/build"
	"go/build/constraint"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"io"
	"os"
	"sort"
	"strings"
)

// input names the donor module and the module directories of its pinned
// dependencies. Deps maps a module path to the directory that holds that
// module at the version the donor's go.mod requires; a dependency that is
// not listed, or whose directory is absent, is represented by an empty
// package, as before.
type input struct {
	Module   string            `json:"module"`
	Files    map[string]string `json:"files"`
	Packages []string          `json:"packages"`
	Deps     map[string]string `json:"deps"`
}

// target is one build context: the platform and the extra build tags.
type buildTarget struct {
	goos, goarch string
	tags         []string
}

func (t buildTarget) key() string {
	return t.goos + "/" + t.goarch + "?" + strings.Join(t.tags, ",")
}

var baseTarget = buildTarget{goos: "linux", goarch: "amd64"}

type outRef [2]string

type outDecl struct {
	Key        string   `json:"key"`
	Name       string   `json:"name"`
	Kind       string   `json:"kind"`
	Receiver   string   `json:"receiver"`
	File       string   `json:"file"`
	Test       bool     `json:"test"`
	Uses       []outRef `json:"uses"`
	Unresolved []string `json:"unresolved,omitempty"`
}

type outAssertion struct {
	Text  string   `json:"text"`
	Uses  []outRef `json:"uses"`
	Calls []outRef `json:"calls"`
}

type outTest struct {
	Name       string         `json:"name"`
	File       string         `json:"file"`
	Uses       []outRef       `json:"uses"`
	Assertions []outAssertion `json:"assertions"`
}

type outPackage struct {
	Dir   string    `json:"dir"`
	Name  string    `json:"name"`
	XTest bool      `json:"xtest"`
	Decls []outDecl `json:"decls"`
	Tests []outTest `json:"tests"`
}

type output struct {
	Errors   []string     `json:"errors"`
	Packages []outPackage `json:"packages"`
}

// ref names a declared symbol: the donor directory (with "#xtest" appended
// for an external test package) and the key, "Name" or "Type.Method".
type ref struct{ Pkg, Key string }

type refset map[ref]struct{}

func (s refset) add(r ref) bool {
	if _, ok := s[r]; ok {
		return false
	}
	s[r] = struct{}{}
	return true
}

func (s refset) union(other refset) bool {
	grew := false
	for r := range other {
		if s.add(r) {
			grew = true
		}
	}
	return grew
}

func (s refset) list() []outRef {
	out := make([]outRef, 0, len(s))
	for r := range s {
		out = append(out, outRef{r.Pkg, r.Key})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i][0] != out[j][0] {
			return out[i][0] < out[j][0]
		}
		return out[i][1] < out[j][1]
	})
	return out
}

type sourceFile struct {
	rel     string
	dir     string
	text    string
	test    bool
	clause  string
	imports []string
	parsed  *ast.File
}

type dirFiles struct {
	dir       string
	base      []*sourceFile
	internal  []*sourceFile
	external  []*sourceFile
	excluded  []*sourceFile
	name      string
	extName   string
	parseDone bool
}

type result struct {
	pkg        *types.Package
	info       *types.Info
	files      []*ast.File
	errs       []string
	unresolved bool
}

type loader struct {
	in       input
	target   buildTarget
	fset     *token.FileSet
	ctxt     build.Context
	deps     map[string]*types.Package
	std      types.ImporterFrom
	dirs     map[string]*dirFiles
	pathDir  map[string]string
	bases    map[string]*result
	variants map[string]*result
	rebuilds map[string]*result
	externs  map[string]*result
	loading  map[string]bool
	fakes    map[string]*types.Package
	errors   []string
}

func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		fmt.Fprintln(os.Stderr, "read:", err)
		os.Exit(2)
	}
	var in input
	if err := json.Unmarshal(data, &in); err != nil {
		fmt.Fprintln(os.Stderr, "input:", err)
		os.Exit(2)
	}
	l := newLoader(in, baseTarget)
	out := l.run()
	encoded, err := json.Marshal(out)
	if err != nil {
		fmt.Fprintln(os.Stderr, "output:", err)
		os.Exit(2)
	}
	os.Stdout.Write(encoded)
	os.Stdout.Write([]byte("\n"))
}

func newLoader(in input, t buildTarget) *loader {
	build.Default.CgoEnabled = false
	build.Default.GOOS = t.goos
	build.Default.GOARCH = t.goarch
	ctxt := build.Default
	ctxt.GOOS = t.goos
	ctxt.GOARCH = t.goarch
	ctxt.BuildTags = append([]string{}, t.tags...)
	ctxt.CgoEnabled = false
	ctxt.OpenFile = func(path string) (io.ReadCloser, error) {
		text, ok := in.Files[strings.TrimPrefix(path, "/donor/")]
		if !ok {
			return nil, os.ErrNotExist
		}
		return io.NopCloser(strings.NewReader(text)), nil
	}
	fset := token.NewFileSet()
	l := &loader{
		in:       in,
		target:   t,
		deps:     map[string]*types.Package{},
		fset:     fset,
		ctxt:     ctxt,
		dirs:     map[string]*dirFiles{},
		pathDir:  map[string]string{},
		bases:    map[string]*result{},
		variants: map[string]*result{},
		rebuilds: map[string]*result{},
		externs:  map[string]*result{},
		loading:  map[string]bool{},
		fakes:    map[string]*types.Package{},
	}
	l.std, _ = importer.ForCompiler(token.NewFileSet(), "source", nil).(types.ImporterFrom)
	l.scan()
	return l
}

func dirOfFile(rel string) string {
	index := strings.LastIndex(rel, "/")
	if index < 0 {
		return "."
	}
	return rel[:index]
}

// scan keeps import edges even for excluded files, so a test that imports
// the moved package only on another build target is not silently ignored.
func (l *loader) scan() {
	names := make([]string, 0, len(l.in.Files))
	for rel := range l.in.Files {
		names = append(names, rel)
	}
	sort.Strings(names)
	for _, rel := range names {
		if !strings.HasSuffix(rel, ".go") {
			continue
		}
		dir := dirOfFile(rel)
		name := rel[strings.LastIndex(rel, "/")+1:]
		if strings.HasPrefix(name, "_") || strings.HasPrefix(name, ".") {
			continue
		}
		match, err := l.ctxt.MatchFile("/donor/"+dir, name)
		head, _ := parser.ParseFile(token.NewFileSet(), rel, l.in.Files[rel], parser.ImportsOnly|parser.SkipObjectResolution)
		file := &sourceFile{rel: rel, dir: dir, text: l.in.Files[rel], test: strings.HasSuffix(rel, "_test.go")}
		if head != nil {
			if head.Name != nil {
				file.clause = head.Name.Name
			}
			for _, spec := range head.Imports {
				path := strings.Trim(spec.Path.Value, "\"`")
				file.imports = append(file.imports, path)
				if path == "C" {
					match = false
				}
			}
		}
		group := l.dirs[dir]
		if group == nil {
			group = &dirFiles{dir: dir}
			l.dirs[dir] = group
		}
		if err != nil || !match {
			group.excluded = append(group.excluded, file)
		} else if !file.test {
			group.base = append(group.base, file)
		} else if strings.HasSuffix(file.clause, "_test") {
			group.external = append(group.external, file)
		} else {
			group.internal = append(group.internal, file)
		}
	}
	for _, group := range l.dirs {
		if len(group.base) > 0 {
			group.name = group.base[0].clause
		} else if len(group.internal) > 0 {
			group.name = group.internal[0].clause
		}
		if len(group.external) > 0 {
			group.extName = group.external[0].clause
		}
	}
}

func (l *loader) importPath(dir string) string {
	if l.in.Module == "" {
		return dir
	}
	if dir == "." {
		return l.in.Module
	}
	return l.in.Module + "/" + dir
}

// donorDir maps an import path to the donor directory that holds its files.
func (l *loader) donorDir(path string) (string, bool) {
	has := func(dir string) bool {
		group := l.dirs[dir]
		if group == nil {
			return false
		}
		if len(group.base) > 0 {
			return true
		}
		for _, file := range group.excluded {
			if !file.test {
				return true
			}
		}
		return false
	}
	module := l.in.Module
	if module != "" {
		if path == module && has(".") {
			return ".", true
		}
		if strings.HasPrefix(path, module+"/") {
			dir := path[len(module)+1:]
			if has(dir) {
				return dir, true
			}
		}
		return "", false
	}
	parts := strings.Split(path, "/")
	for index := range parts {
		dir := strings.Join(parts[index:], "/")
		if has(dir) {
			return dir, true
		}
	}
	return "", false
}

func (l *loader) parseFiles(files []*sourceFile) ([]*ast.File, []string) {
	var out []*ast.File
	var errs []string
	for _, file := range files {
		if file.parsed == nil {
			parsed, err := parser.ParseFile(l.fset, file.rel, file.text, parser.SkipObjectResolution)
			if err != nil {
				errs = append(errs, "parse-error: "+err.Error())
			}
			if parsed == nil {
				continue
			}
			file.parsed = parsed
		}
		out = append(out, file.parsed)
	}
	return out, errs
}

type donorImporter struct {
	l     *loader
	owner *result
	// variantOf names a directory whose test variant stands for its import
	// path: an external test package imports the package under test with its
	// internal test files.
	variantOf string
}

func (i *donorImporter) Import(path string) (*types.Package, error) {
	l := i.l
	if dir, ok := l.donorDir(path); ok {
		var imported *result
		switch {
		case dir == i.variantOf:
			imported = l.variant(dir)
		case i.variantOf != "" && l.reachesNamed(dir, map[string]bool{i.variantOf: true}, map[string]bool{}):
			imported = l.rebuilt(dir, i.variantOf)
		default:
			imported = l.base(dir)
		}
		if imported == nil || imported.pkg == nil {
			i.owner.unresolved = true
			return l.fake(path), nil
		}
		if imported.unresolved {
			i.owner.unresolved = true
		}
		return imported.pkg, nil
	}
	if pkg := l.dependency(path); pkg != nil {
		return pkg, nil
	}
	if pkg := l.standard(path); pkg != nil {
		return pkg, nil
	}
	i.owner.unresolved = true
	return l.fake(path), nil
}

func (l *loader) standard(path string) *types.Package {
	if l.std == nil || strings.Contains(strings.SplitN(path, "/", 2)[0], ".") {
		return nil
	}
	pkg, err := l.std.ImportFrom(path, "", 0)
	if err != nil {
		return nil
	}
	return pkg
}

// libraryImporter resolves the imports of a dependency: another dependency,
// the standard library, or an empty package.
type libraryImporter struct{ l *loader }

func (i libraryImporter) Import(path string) (*types.Package, error) {
	if pkg := i.l.dependency(path); pkg != nil {
		return pkg, nil
	}
	if pkg := i.l.standard(path); pkg != nil {
		return pkg, nil
	}
	return i.l.fake(path), nil
}

// dependency type-checks a package of a pinned dependency from the module
// directory the input names for it, for the loader's build target, without
// its test files and without function bodies. It returns nil when the
// package is not a dependency the input resolves.
func (l *loader) dependency(path string) *types.Package {
	if pkg, seen := l.deps[path]; seen {
		return pkg
	}
	l.deps[path] = nil
	module, root := "", ""
	for name, dir := range l.in.Deps {
		if (path == name || strings.HasPrefix(path, name+"/")) && len(name) > len(module) {
			module, root = name, dir
		}
	}
	if module == "" {
		return nil
	}
	dir := root + strings.TrimPrefix(path, module)
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	ctxt := l.ctxt
	ctxt.OpenFile = nil
	var files []*ast.File
	for _, entry := range entries {
		name := entry.Name()
		if entry.IsDir() || !strings.HasSuffix(name, ".go") || strings.HasSuffix(name, "_test.go") ||
			strings.HasPrefix(name, "_") || strings.HasPrefix(name, ".") {
			continue
		}
		if match, err := ctxt.MatchFile(dir, name); err != nil || !match {
			continue
		}
		parsed, err := parser.ParseFile(l.fset, dir+"/"+name, nil, parser.SkipObjectResolution)
		if err != nil || parsed == nil {
			continue
		}
		cgo := false
		for _, spec := range parsed.Imports {
			if strings.Trim(spec.Path.Value, "\"`") == "C" {
				cgo = true
			}
		}
		if !cgo {
			files = append(files, parsed)
		}
	}
	if len(files) == 0 {
		return nil
	}
	conf := types.Config{
		Importer:         libraryImporter{l},
		FakeImportC:      true,
		IgnoreFuncBodies: true,
		Sizes:            types.SizesFor("gc", l.target.goarch),
		Error:            func(error) {},
	}
	pkg, _ := conf.Check(path, l.fset, files, nil)
	l.deps[path] = pkg
	return pkg
}

func (l *loader) fake(path string) *types.Package {
	if pkg, ok := l.fakes[path]; ok {
		return pkg
	}
	parts := strings.Split(path, "/")
	name := parts[len(parts)-1]
	if len(parts) > 1 && len(name) > 1 && name[0] == 'v' && strings.Trim(name[1:], "0123456789") == "" {
		name = parts[len(parts)-2]
	}
	name = strings.NewReplacer("-", "_", ".", "_").Replace(strings.TrimPrefix(name, "go-"))
	pkg := types.NewPackage(path, name)
	pkg.MarkComplete()
	l.fakes[path] = pkg
	return pkg
}

func (l *loader) check(path string, files []*ast.File, info *types.Info, imp *donorImporter, owner *result) {
	conf := types.Config{
		Importer:    imp,
		FakeImportC: true,
		Sizes:       types.SizesFor("gc", l.target.goarch),
		Error: func(err error) {
			if typed, ok := err.(types.Error); ok && !typed.Soft {
				owner.errs = append(owner.errs, typed.Error())
			}
		},
	}
	owner.pkg, _ = conf.Check(path, l.fset, files, info)
}

func newInfo() *types.Info {
	return &types.Info{
		Defs:       map[*ast.Ident]types.Object{},
		Uses:       map[*ast.Ident]types.Object{},
		Implicits:  map[ast.Node]types.Object{},
		Selections: map[*ast.SelectorExpr]*types.Selection{},
	}
}

func (l *loader) base(dir string) *result {
	if found, ok := l.bases[dir]; ok {
		return found
	}
	group := l.dirs[dir]
	if group == nil || len(group.base) == 0 || l.loading["base:"+dir] {
		return nil
	}
	l.loading["base:"+dir] = true
	defer delete(l.loading, "base:"+dir)
	owner := &result{}
	l.bases[dir] = owner
	files, errs := l.parseFiles(group.base)
	owner.errs = append(owner.errs, errs...)
	owner.files = files
	path := l.importPath(dir)
	l.pathDir[path] = dir
	l.check(path, files, &types.Info{}, &donorImporter{l: l, owner: owner}, owner)
	return owner
}

// rebuilt is a package of a directory checked against the test variant of
// the package under test: a package that imports that package must see the
// variant's types, as the toolchain recompiles it for the test binary.
func (l *loader) rebuilt(dir, under string) *result {
	key := under + "|" + dir
	if found, ok := l.rebuilds[key]; ok {
		return found
	}
	group := l.dirs[dir]
	if group == nil || len(group.base) == 0 || l.loading["rebuilt:"+key] {
		return nil
	}
	l.loading["rebuilt:"+key] = true
	defer delete(l.loading, "rebuilt:"+key)
	owner := &result{}
	l.rebuilds[key] = owner
	files, errs := l.parseFiles(group.base)
	owner.errs = append(owner.errs, errs...)
	owner.files = files
	l.check(l.importPath(dir), files, &types.Info{}, &donorImporter{l: l, owner: owner, variantOf: under}, owner)
	return owner
}

// variant is the package of a directory with its internal test files.
func (l *loader) variant(dir string) *result {
	if found, ok := l.variants[dir]; ok {
		return found
	}
	group := l.dirs[dir]
	if group == nil || l.loading["variant:"+dir] {
		return nil
	}
	l.loading["variant:"+dir] = true
	defer delete(l.loading, "variant:"+dir)
	owner := &result{info: newInfo()}
	l.variants[dir] = owner
	all := append(append([]*sourceFile{}, group.base...), group.internal...)
	files, errs := l.parseFiles(all)
	owner.errs = append(owner.errs, errs...)
	owner.files = files
	path := l.importPath(dir)
	l.pathDir[path] = dir
	l.check(path, files, owner.info, &donorImporter{l: l, owner: owner}, owner)
	return owner
}

func (l *loader) external(dir string) *result {
	if found, ok := l.externs[dir]; ok {
		return found
	}
	group := l.dirs[dir]
	if group == nil || len(group.external) == 0 {
		return nil
	}
	owner := &result{info: newInfo()}
	l.externs[dir] = owner
	files, errs := l.parseFiles(group.external)
	owner.errs = append(owner.errs, errs...)
	owner.files = files
	path := l.importPath(dir) + "_test"
	l.pathDir[path] = dir + "#xtest"
	l.check(path, files, owner.info, &donorImporter{l: l, owner: owner, variantOf: dir}, owner)
	return owner
}

// reachesNamed reports whether the package files of dir import, directly or
// through other donor packages, a donor directory the move names.
func (l *loader) reachesNamed(dir string, named map[string]bool, visited map[string]bool) bool {
	if named[dir] {
		return true
	}
	if visited[dir] {
		return false
	}
	visited[dir] = true
	group := l.dirs[dir]
	if group == nil {
		return false
	}
	for _, file := range append(append([]*sourceFile{}, group.base...), group.excluded...) {
		if file.test {
			continue
		}
		for _, path := range file.imports {
			if target, ok := l.donorDir(path); ok && l.reachesNamed(target, named, visited) {
				return true
			}
		}
	}
	return false
}

func (l *loader) run() output {
	l.activate()
	out := output{Errors: []string{}, Packages: []outPackage{}}
	named := map[string]bool{}
	for _, dir := range l.in.Packages {
		named[dir] = true
	}
	var selected []string
	for dir, group := range l.dirs {
		if named[dir] {
			selected = append(selected, dir)
			continue
		}
		// A directory whose tests can reach a package of the move holds tests
		// of it: a test file imports it, or imports a package that imports it,
		// or the directory's own package does. A value of a type of the move
		// can only come through such a chain of imports, so a test that calls
		// a method of it need not import the package itself.
		tests := append(append([]*sourceFile{}, group.internal...), group.external...)
		for _, file := range group.excluded {
			if file.test {
				tests = append(tests, file)
			}
		}
		if len(tests) == 0 {
			continue
		}
		reached := l.reachesNamed(dir, named, map[string]bool{})
		for _, file := range tests {
			if reached {
				break
			}
			for _, path := range file.imports {
				if target, ok := l.donorDir(path); ok && l.reachesNamed(target, named, map[string]bool{}) {
					reached = true
					break
				}
			}
		}
		if reached {
			selected = append(selected, dir)
		}
	}
	sort.Strings(selected)
	var excluded []*sourceFile
	for _, dir := range selected {
		excluded = append(excluded, l.dirs[dir].excluded...)
		for _, kind := range []string{"variant", "external"} {
			var res *result
			xtest := kind == "external"
			if xtest {
				res = l.external(dir)
			} else {
				res = l.variant(dir)
			}
			if res == nil || res.pkg == nil {
				continue
			}
			label := dir
			if xtest {
				label = dir + "#xtest"
			}
			if len(res.errs) > 0 && !res.unresolved {
				limit := res.errs
				if len(limit) > 5 {
					limit = limit[:5]
				}
				for _, text := range limit {
					out.Errors = append(out.Errors, "type-error: "+label+": "+text)
				}
			}
			analyzer := &analyzer{l: l, info: res.info, unresolved: res.unresolved}
			out.Packages = append(out.Packages, analyzer.report(dir, res, xtest))
		}
	}
	fragments, unaccounted := l.account(excluded)
	for _, rel := range unaccounted {
		out.Errors = append(out.Errors, "unsupported-build-file: "+rel)
	}
	for _, fragment := range fragments {
		merged := false
		for index := range out.Packages {
			have := &out.Packages[index]
			if have.Dir == fragment.Dir && have.XTest == fragment.XTest {
				have.Decls = append(have.Decls, fragment.Decls...)
				have.Tests = append(have.Tests, fragment.Tests...)
				sortPackage(have)
				merged = true
				break
			}
		}
		if !merged {
			out.Packages = append(out.Packages, fragment)
		}
	}
	sort.Strings(out.Errors)
	return out
}

var knownTargetTags = map[string]bool{
	"aix": true, "android": true, "darwin": true, "dragonfly": true, "freebsd": true, "hurd": true,
	"illumos": true, "ios": true, "js": true, "linux": true, "nacl": true, "netbsd": true, "openbsd": true,
	"plan9": true, "solaris": true, "wasip1": true, "windows": true, "zos": true,
	"386": true, "amd64": true, "arm": true, "arm64": true, "loong64": true, "mips": true, "mips64": true,
	"mips64le": true, "mipsle": true, "ppc64": true, "ppc64le": true, "riscv64": true, "s390x": true, "wasm": true,
	"unix": true, "cgo": true, "gc": true, "gccgo": true, "ignore": true,
}

var accountOS = []string{"linux", "darwin", "windows", "freebsd", "netbsd", "openbsd", "dragonfly", "solaris", "illumos", "aix", "plan9", "android", "ios"}

var accountArch = []string{"amd64", "arm64", "386", "arm", "ppc64le", "s390x", "riscv64", "mips"}

func collectTags(expr constraint.Expr, into map[string]bool) {
	switch item := expr.(type) {
	case *constraint.AndExpr:
		collectTags(item.X, into)
		collectTags(item.Y, into)
	case *constraint.OrExpr:
		collectTags(item.X, into)
		collectTags(item.Y, into)
	case *constraint.NotExpr:
		collectTags(item.X, into)
	case *constraint.TagExpr:
		into[item.Tag] = true
	}
}

// constraintTags are the custom build tags a file's constraint lines name:
// not a platform, not a toolchain tag, and never "ignore".
func constraintTags(text string) []string {
	seen := map[string]bool{}
	for _, line := range strings.Split(text, "\n") {
		trimmed := strings.TrimSpace(line)
		if strings.HasPrefix(trimmed, "package ") {
			break
		}
		if !constraint.IsGoBuild(trimmed) && !constraint.IsPlusBuild(trimmed) {
			continue
		}
		if expr, err := constraint.Parse(trimmed); err == nil {
			collectTags(expr, seen)
		}
	}
	var out []string
	for tag := range seen {
		if !knownTargetTags[tag] && !strings.HasPrefix(tag, "go1.") && !strings.HasPrefix(tag, "goexperiment.") {
			out = append(out, tag)
		}
	}
	sort.Strings(out)
	return out
}

// targetFor finds the first build context in which the loader's own context
// excludes file but the file is part of its package: the base platform with
// the custom tags the file names, then another architecture, then another
// operating system. A file with no such context has none.
func (l *loader) targetFor(file *sourceFile) (buildTarget, bool) {
	for _, path := range file.imports {
		if path == "C" {
			return buildTarget{}, false
		}
	}
	tags := constraintTags(file.text)
	if len(tags) > 8 {
		return buildTarget{}, false
	}
	var subsets [][]string
	for mask := 0; mask < 1<<len(tags); mask++ {
		var subset []string
		for index, tag := range tags {
			if mask&(1<<index) != 0 {
				subset = append(subset, tag)
			}
		}
		subsets = append(subsets, subset)
	}
	sort.SliceStable(subsets, func(i, j int) bool { return len(subsets[i]) < len(subsets[j]) })
	name := file.rel[strings.LastIndex(file.rel, "/")+1:]
	for _, subset := range subsets {
		for _, goos := range accountOS {
			for _, goarch := range accountArch {
				candidate := buildTarget{goos: goos, goarch: goarch, tags: subset}
				ctxt := l.ctxt
				ctxt.GOOS, ctxt.GOARCH, ctxt.BuildTags = goos, goarch, subset
				if match, err := ctxt.MatchFile("/donor/"+file.dir, name); err == nil && match {
					return candidate, true
				}
			}
		}
	}
	return buildTarget{}, false
}

func sortPackage(pkg *outPackage) {
	sort.Slice(pkg.Decls, func(i, j int) bool {
		if pkg.Decls[i].File != pkg.Decls[j].File {
			return pkg.Decls[i].File < pkg.Decls[j].File
		}
		return pkg.Decls[i].Key < pkg.Decls[j].Key
	})
	sort.Slice(pkg.Tests, func(i, j int) bool {
		if pkg.Tests[i].File != pkg.Tests[j].File {
			return pkg.Tests[i].File < pkg.Tests[j].File
		}
		return pkg.Tests[i].Name < pkg.Tests[j].Name
	})
}

// account takes the files the base build excludes and type-checks each in
// the first other build context that includes it. A file is accounted for
// when its package checks there; the declarations and tests of the accounted
// files are returned as package fragments, so the closure reads what they
// use. A file that no context includes, that imports C, whose clause differs
// from its package or whose package does not check in its context is
// returned as unaccounted.
func (l *loader) account(files []*sourceFile) ([]outPackage, []string) {
	groups := map[string][]*sourceFile{}
	targets := map[string]buildTarget{}
	var unaccounted []string
	for _, file := range files {
		chosen, ok := l.targetFor(file)
		if !ok {
			unaccounted = append(unaccounted, file.rel)
			continue
		}
		key := chosen.key()
		groups[key] = append(groups[key], file)
		targets[key] = chosen
	}
	keys := make([]string, 0, len(groups))
	for key := range groups {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	var fragments []outPackage
	for _, key := range keys {
		other := newLoader(l.in, targets[key])
		found, failed := other.accounted(groups[key])
		fragments = append(fragments, found...)
		unaccounted = append(unaccounted, failed...)
	}
	l.activate()
	sort.Strings(unaccounted)
	return fragments, unaccounted
}

// activate points the standard library importer at the loader's platform.
func (l *loader) activate() {
	build.Default.CgoEnabled = false
	build.Default.GOOS = l.target.goos
	build.Default.GOARCH = l.target.goarch
}

func (l *loader) accounted(files []*sourceFile) ([]outPackage, []string) {
	want := map[string]bool{}
	for _, file := range files {
		want[file.rel] = true
	}
	var failed []string
	var out []outPackage
	type unit struct {
		dir   string
		xtest bool
	}
	checked := map[unit]*outPackage{}
	for _, file := range files {
		group := l.dirs[file.dir]
		var kind []*sourceFile
		xtest := false
		for _, candidate := range [][]*sourceFile{group.base, group.internal, group.external} {
			for _, item := range candidate {
				if item.rel == file.rel {
					kind = candidate
				}
			}
		}
		if kind == nil {
			failed = append(failed, file.rel)
			continue
		}
		xtest = len(group.external) > 0 && kind[0] == group.external[0]
		clause := group.name
		if xtest {
			clause = group.extName
		}
		for _, item := range kind {
			if item.clause != clause {
				kind = nil
			}
		}
		if kind == nil {
			failed = append(failed, file.rel)
			continue
		}
		key := unit{file.dir, xtest}
		fragment, done := checked[key]
		if !done {
			var res *result
			if xtest {
				res = l.external(file.dir)
			} else {
				res = l.variant(file.dir)
			}
			if res != nil && res.pkg != nil && !res.failed() {
				analyzer := &analyzer{l: l, info: res.info, unresolved: res.unresolved}
				report := analyzer.report(file.dir, res, xtest)
				report.Decls = keepDecls(report.Decls, want)
				report.Tests = keepTests(report.Tests, want)
				fragment = &report
			}
			checked[key] = fragment
		}
		if fragment == nil {
			failed = append(failed, file.rel)
		}
	}
	units := make([]unit, 0, len(checked))
	for key, fragment := range checked {
		if fragment != nil {
			units = append(units, key)
		}
	}
	sort.Slice(units, func(i, j int) bool {
		if units[i].dir != units[j].dir {
			return units[i].dir < units[j].dir
		}
		return !units[i].xtest && units[j].xtest
	})
	for _, key := range units {
		out = append(out, *checked[key])
	}
	return out, failed
}

func keepDecls(decls []outDecl, want map[string]bool) []outDecl {
	kept := []outDecl{}
	for _, decl := range decls {
		if want[decl.File] {
			kept = append(kept, decl)
		}
	}
	return kept
}

func keepTests(tests []outTest, want map[string]bool) []outTest {
	kept := []outTest{}
	for _, test := range tests {
		if want[test.File] {
			kept = append(kept, test)
		}
	}
	return kept
}

// failed reports a package that does not parse, or that does not check
// although everything it imports resolved.
func (r *result) failed() bool {
	for _, text := range r.errs {
		if strings.HasPrefix(text, "parse-error: ") {
			return true
		}
	}
	return len(r.errs) > 0 && !r.unresolved
}

type analyzer struct {
	l    *loader
	info *types.Info
	// unresolved is set when the package imports something that is neither
	// the standard library nor a donor package, so the type of a value that
	// comes from it is unknown.
	unresolved bool
}

func unparen(expr ast.Expr) ast.Expr {
	for {
		paren, ok := expr.(*ast.ParenExpr)
		if !ok {
			return expr
		}
		expr = paren.X
	}
}

// ref reports the declared symbol an object stands for, if it is a package
// level declaration of a donor package.
func (a *analyzer) ref(obj types.Object) (ref, bool) {
	if obj == nil || obj.Pkg() == nil {
		return ref{}, false
	}
	switch object := obj.(type) {
	case *types.Var:
		if object.IsField() || object.Parent() != object.Pkg().Scope() {
			return ref{}, false
		}
		return a.at(object.Pkg(), object.Name())
	case *types.Const:
		if object.Parent() != object.Pkg().Scope() {
			return ref{}, false
		}
		return a.at(object.Pkg(), object.Name())
	case *types.TypeName:
		if object.Parent() != object.Pkg().Scope() {
			return ref{}, false
		}
		return a.at(object.Pkg(), object.Name())
	case *types.Func:
		object = object.Origin()
		signature, ok := object.Type().(*types.Signature)
		if !ok {
			return ref{}, false
		}
		receiver := signature.Recv()
		if receiver == nil {
			if object.Parent() != object.Pkg().Scope() {
				return ref{}, false
			}
			return a.at(object.Pkg(), object.Name())
		}
		recvType := types.Unalias(receiver.Type())
		if pointer, ok := recvType.(*types.Pointer); ok {
			recvType = types.Unalias(pointer.Elem())
		}
		named, ok := recvType.(*types.Named)
		if !ok {
			return ref{}, false
		}
		owner := named.Origin().Obj()
		if owner.Pkg() == nil || owner.Parent() != owner.Pkg().Scope() {
			return ref{}, false
		}
		if types.IsInterface(named) {
			// An interface method is a use of the interface type.
			return a.at(owner.Pkg(), owner.Name())
		}
		return a.at(owner.Pkg(), owner.Name()+"."+object.Name())
	}
	return ref{}, false
}

func (a *analyzer) at(pkg *types.Package, key string) (ref, bool) {
	dir, ok := a.l.pathDir[pkg.Path()]
	if !ok {
		return ref{}, false
	}
	return ref{dir, key}, true
}

func (a *analyzer) local(obj types.Object) bool {
	if obj == nil || obj.Pkg() == nil {
		return false
	}
	switch object := obj.(type) {
	case *types.Var:
		return !object.IsField() && object.Parent() != object.Pkg().Scope()
	case *types.Const:
		return object.Parent() != object.Pkg().Scope()
	case *types.TypeName:
		return object.Parent() != object.Pkg().Scope()
	}
	return false
}

// direct adds the declared symbols the identifiers under node resolve to.
func (a *analyzer) direct(node ast.Node, into refset) {
	if node == nil {
		return
	}
	ast.Inspect(node, func(item ast.Node) bool {
		if id, ok := item.(*ast.Ident); ok {
			if found, ok := a.ref(a.info.Uses[id]); ok {
				into.add(found)
			}
		}
		return true
	})
}

// A missing receiver type is not evidence for any particular donor method.
func (a *analyzer) unresolvedSelectors(node ast.Node) []string {
	if !a.unresolved || node == nil {
		return nil
	}
	names := map[string]bool{}
	ast.Inspect(node, func(node ast.Node) bool {
		sel, ok := node.(*ast.SelectorExpr)
		if !ok || a.info.Uses[sel.Sel] != nil || a.info.Selections[sel] != nil {
			return true
		}
		if id, ok := unparen(sel.X).(*ast.Ident); ok {
			if _, qualified := a.info.Uses[id].(*types.PkgName); qualified {
				return true
			}
		}
		names[sel.Sel.Name] = true
		return true
	})
	var out []string
	for name := range names {
		out = append(out, name)
	}
	sort.Strings(out)
	return out
}

func (a *analyzer) calls(node ast.Node, into refset) {
	ast.Inspect(node, func(item ast.Node) bool {
		call, ok := item.(*ast.CallExpr)
		if !ok {
			return true
		}
		fun := unparen(call.Fun)
		for {
			switch inner := fun.(type) {
			case *ast.IndexExpr:
				fun = unparen(inner.X)
				continue
			case *ast.IndexListExpr:
				fun = unparen(inner.X)
				continue
			}
			break
		}
		var id *ast.Ident
		switch target := fun.(type) {
		case *ast.Ident:
			id = target
		case *ast.SelectorExpr:
			id = target.Sel
		}
		if id != nil {
			if found, ok := a.ref(a.info.Uses[id]); ok {
				into.add(found)
			}
		}
		return true
	})
}

func receiverName(expr ast.Expr) string {
	for {
		switch item := expr.(type) {
		case *ast.ParenExpr:
			expr = item.X
		case *ast.StarExpr:
			expr = item.X
		case *ast.IndexExpr:
			expr = item.X
		case *ast.IndexListExpr:
			expr = item.X
		case *ast.Ident:
			return item.Name
		default:
			return ""
		}
	}
}

// receiverOf names the type a method belongs to as the type checker resolves
// it, so a method written on an alias of a type is a method of that type, as
// a reference to it is read.
func (a *analyzer) receiverOf(decl *ast.FuncDecl) string {
	if fn, ok := a.info.Defs[decl.Name].(*types.Func); ok {
		if signature, ok := fn.Type().(*types.Signature); ok && signature.Recv() != nil {
			recvType := types.Unalias(signature.Recv().Type())
			if pointer, ok := recvType.(*types.Pointer); ok {
				recvType = types.Unalias(pointer.Elem())
			}
			if named, ok := recvType.(*types.Named); ok {
				return named.Origin().Obj().Name()
			}
		}
	}
	return receiverName(decl.Recv.List[0].Type)
}

func (a *analyzer) report(dir string, res *result, xtest bool) outPackage {
	pkg := outPackage{Dir: dir, Name: res.pkg.Name(), XTest: xtest, Decls: []outDecl{}, Tests: []outTest{}}
	for _, file := range res.files {
		name := a.l.fset.Position(file.Pos()).Filename
		isTest := strings.HasSuffix(name, "_test.go")
		for _, decl := range file.Decls {
			switch item := decl.(type) {
			case *ast.FuncDecl:
				if item.Name.Name == "_" || item.Name.Name == "init" && item.Recv == nil {
					continue
				}
				uses := refset{}
				a.direct(item, uses)
				record := outDecl{Key: item.Name.Name, Name: item.Name.Name, Kind: "func", File: name, Test: isTest}
				if item.Recv != nil && len(item.Recv.List) == 1 {
					record.Kind = "method"
					record.Receiver = a.receiverOf(item)
					record.Key = record.Receiver + "." + item.Name.Name
				}
				record.Uses = uses.list()
				record.Unresolved = a.unresolvedSelectors(item)
				pkg.Decls = append(pkg.Decls, record)
				if isTest && item.Recv == nil && strings.HasPrefix(item.Name.Name, "Test") && item.Body != nil {
					pkg.Tests = append(pkg.Tests, a.test(item, name))
				}
			case *ast.GenDecl:
				pkg.Decls = append(pkg.Decls, a.generalDecls(item, name, isTest)...)
			}
		}
	}
	sort.Slice(pkg.Decls, func(i, j int) bool {
		if pkg.Decls[i].File != pkg.Decls[j].File {
			return pkg.Decls[i].File < pkg.Decls[j].File
		}
		return pkg.Decls[i].Key < pkg.Decls[j].Key
	})
	sort.Slice(pkg.Tests, func(i, j int) bool {
		if pkg.Tests[i].File != pkg.Tests[j].File {
			return pkg.Tests[i].File < pkg.Tests[j].File
		}
		return pkg.Tests[i].Name < pkg.Tests[j].Name
	})
	return pkg
}

func (a *analyzer) generalDecls(decl *ast.GenDecl, file string, isTest bool) []outDecl {
	var out []outDecl
	var inherit *ast.ValueSpec
	for _, spec := range decl.Specs {
		switch item := spec.(type) {
		case *ast.TypeSpec:
			uses := refset{}
			a.direct(item, uses)
			out = append(out, outDecl{Key: item.Name.Name, Name: item.Name.Name, Kind: "type", File: file, Test: isTest, Uses: uses.list(), Unresolved: a.unresolvedSelectors(item)})
		case *ast.ValueSpec:
			kind := "var"
			source := item
			if decl.Tok == token.CONST {
				kind = "const"
				if item.Type != nil || len(item.Values) > 0 {
					inherit = item
				} else if inherit != nil {
					// A constant without an expression repeats the
					// specification before it.
					source = inherit
				}
			}
			for index, name := range item.Names {
				if name.Name == "_" {
					continue
				}
				uses := refset{}
				a.direct(source.Type, uses)
				values := source.Values
				if len(values) == len(item.Names) {
					values = values[index : index+1]
				}
				unresolved := a.unresolvedSelectors(source.Type)
				for _, value := range values {
					a.direct(value, uses)
					unresolved = append(unresolved, a.unresolvedSelectors(value)...)
				}
				out = append(out, outDecl{Key: name.Name, Name: name.Name, Kind: kind, File: file, Test: isTest, Uses: uses.list(), Unresolved: unresolved})
			}
		}
	}
	return out
}
