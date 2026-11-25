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
// two is replaced by an empty package of its name, and the diagnostics that
// follow from that are not reported.
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/build"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"io"
	"os"
	"sort"
	"strings"
)

type input struct {
	Module   string            `json:"module"`
	Files    map[string]string `json:"files"`
	Packages []string          `json:"packages"`
}

type outRef [2]string

type outDecl struct {
	Key      string   `json:"key"`
	Name     string   `json:"name"`
	Kind     string   `json:"kind"`
	Receiver string   `json:"receiver"`
	File     string   `json:"file"`
	Test     bool     `json:"test"`
	Uses     []outRef `json:"uses"`
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
	fset     *token.FileSet
	ctxt     build.Context
	std      types.ImporterFrom
	dirs     map[string]*dirFiles
	pathDir  map[string]string
	bases    map[string]*result
	variants map[string]*result
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
	l := newLoader(in)
	out := l.run()
	encoded, err := json.Marshal(out)
	if err != nil {
		fmt.Fprintln(os.Stderr, "output:", err)
		os.Exit(2)
	}
	os.Stdout.Write(encoded)
	os.Stdout.Write([]byte("\n"))
}

func newLoader(in input) *loader {
	build.Default.CgoEnabled = false
	ctxt := build.Default
	ctxt.GOOS = "linux"
	ctxt.GOARCH = "amd64"
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
		fset:     fset,
		ctxt:     ctxt,
		dirs:     map[string]*dirFiles{},
		pathDir:  map[string]string{},
		bases:    map[string]*result{},
		variants: map[string]*result{},
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

// scan reads the package clause and the imports of every Go file the build
// constraints of linux/amd64 admit.
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
		match, err := l.ctxt.MatchFile("/donor/"+dir, name)
		if err != nil || !match {
			continue
		}
		head, err := parser.ParseFile(token.NewFileSet(), rel, l.in.Files[rel], parser.ImportsOnly|parser.SkipObjectResolution)
		if head == nil || head.Name == nil {
			_ = err
			continue
		}
		file := &sourceFile{rel: rel, dir: dir, text: l.in.Files[rel], test: strings.HasSuffix(rel, "_test.go"), clause: head.Name.Name}
		for _, spec := range head.Imports {
			path := strings.Trim(spec.Path.Value, "\"`")
			file.imports = append(file.imports, path)
		}
		group := l.dirs[dir]
		if group == nil {
			group = &dirFiles{dir: dir}
			l.dirs[dir] = group
		}
		if !file.test {
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
		return group != nil && len(group.base) > 0
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
		if dir == i.variantOf {
			imported = l.variant(dir)
		} else {
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
	if l.std != nil && !strings.Contains(strings.SplitN(path, "/", 2)[0], ".") {
		if pkg, err := l.std.ImportFrom(path, "", 0); err == nil && pkg != nil {
			return pkg, nil
		}
	}
	i.owner.unresolved = true
	return l.fake(path), nil
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
		Sizes:       types.SizesFor("gc", "amd64"),
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
	for _, file := range group.base {
		for _, path := range file.imports {
			if target, ok := l.donorDir(path); ok && l.reachesNamed(target, named, visited) {
				return true
			}
		}
	}
	return false
}

func (l *loader) run() output {
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
	for _, dir := range selected {
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
			analyzer := &analyzer{l: l, info: res.info, pkg: res.pkg, unresolved: res.unresolved}
			out.Packages = append(out.Packages, analyzer.report(dir, res, xtest))
		}
	}
	sort.Strings(out.Errors)
	return out
}

type analyzer struct {
	l    *loader
	info *types.Info
	pkg  *types.Package
	// unresolved is set when the package imports something that is neither
	// the standard library nor a donor package, so the type of a value that
	// comes from it is unknown.
	unresolved bool
	reachable  []*types.Package
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
		switch found := item.(type) {
		case *ast.Ident:
			if found, ok := a.ref(a.info.Uses[found]); ok {
				into.add(found)
			}
		case *ast.SelectorExpr:
			a.opaque(found, into)
		}
		return true
	})
}

// opaque adds, for a selector whose operand has no type because it comes from
// a package that is not available, every method of that name that a donor
// type of the package's imports declares. The call may reach any of them, so
// none may be left out of the closure.
func (a *analyzer) opaque(sel *ast.SelectorExpr, into refset) {
	if !a.unresolved || a.info.Uses[sel.Sel] != nil || a.info.Selections[sel] != nil {
		return
	}
	if id, ok := unparen(sel.X).(*ast.Ident); ok {
		if _, qualified := a.info.Uses[id].(*types.PkgName); qualified {
			return
		}
	}
	if a.reachable == nil {
		seen := map[*types.Package]bool{}
		var walk func(pkg *types.Package)
		walk = func(pkg *types.Package) {
			if pkg == nil || seen[pkg] {
				return
			}
			seen[pkg] = true
			if _, ok := a.l.pathDir[pkg.Path()]; ok {
				a.reachable = append(a.reachable, pkg)
			}
			for _, imported := range pkg.Imports() {
				walk(imported)
			}
		}
		walk(a.pkg)
		if a.reachable == nil {
			a.reachable = []*types.Package{}
		}
	}
	for _, pkg := range a.reachable {
		scope := pkg.Scope()
		for _, name := range scope.Names() {
			owner, ok := scope.Lookup(name).(*types.TypeName)
			if !ok || owner.IsAlias() || types.IsInterface(owner.Type()) {
				continue
			}
			named, ok := owner.Type().(*types.Named)
			if !ok {
				continue
			}
			for index := 0; index < named.NumMethods(); index++ {
				if method := named.Method(index); method.Name() == sel.Sel.Name {
					if found, ok := a.at(pkg, owner.Name()+"."+method.Name()); ok {
						into.add(found)
					}
				}
			}
		}
	}
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
			out = append(out, outDecl{Key: item.Name.Name, Name: item.Name.Name, Kind: "type", File: file, Test: isTest, Uses: uses.list()})
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
				if len(source.Values) == len(item.Names) {
					a.direct(source.Values[index], uses)
				} else {
					for _, value := range source.Values {
						a.direct(value, uses)
					}
				}
				out = append(out, outDecl{Key: name.Name, Name: name.Name, Kind: kind, File: file, Test: isTest, Uses: uses.list()})
			}
		}
	}
	return out
}
