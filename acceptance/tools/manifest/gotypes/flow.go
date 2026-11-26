package main

import (
	"go/ast"
	"go/token"
	"go/types"
)

var failureNames = map[string]bool{
	"Error": true, "Errorf": true, "Fatal": true, "Fatalf": true, "Fail": true, "FailNow": true,
}

// test reports one test function: the symbols it uses, and for each of its
// top-level checks the symbols the check exercises. A check exercises the
// symbols it names and the symbols of the statements that give the local
// values it reads their values, where those statements can reach the check.
func (a *analyzer) test(decl *ast.FuncDecl, file string) outTest {
	uses := refset{}
	a.direct(decl, uses)
	out := outTest{Name: decl.Name.Name, File: file, Uses: uses.list(), Assertions: []outAssertion{}}
	var checks []*ast.IfStmt
	for _, stmt := range decl.Body.List {
		item, ok := stmt.(*ast.IfStmt)
		if !ok || !failureCall(item) {
			continue
		}
		checks = append(checks, item)
	}
	if len(checks) == 0 {
		return out
	}
	flow := newFlow(a, checks)
	flow.run(decl.Body)
	for _, item := range checks {
		reach := refset{}
		a.direct(item, reach)
		entry := flow.snaps[item]
		written := writeTargets(item)
		ast.Inspect(item, func(node ast.Node) bool {
			if star, ok := node.(*ast.StarExpr); ok && flow.readPointees(star, entry, reach) {
				return false
			}
			id, ok := node.(*ast.Ident)
			if !ok || written[id] {
				return true
			}
			obj := a.info.Uses[id]
			if !a.local(obj) || (obj.Pos() >= item.Pos() && obj.Pos() < item.End()) {
				return true
			}
			for def := range entry[obj] {
				reach.union(def.refs)
			}
			return true
		})
		calls := refset{}
		a.calls(item, calls)
		start := a.l.fset.Position(item.Pos()).Offset
		end := a.l.fset.Position(item.End()).Offset
		text := a.l.sourceOf(file)
		if start >= 0 && end <= len(text) && start <= end {
			text = text[start:end]
		} else {
			text = ""
		}
		out.Assertions = append(out.Assertions, outAssertion{Text: text, Uses: reach.list(), Calls: calls.list()})
	}
	return out
}

func (l *loader) sourceOf(rel string) string {
	return l.in.Files[rel]
}

// writeTargets are the identifiers a plain assignment or a range clause only
// assigns to: they are written, not read, so they do not bring in the
// statements that gave the local its earlier values.
func writeTargets(node ast.Node) map[*ast.Ident]bool {
	out := map[*ast.Ident]bool{}
	ast.Inspect(node, func(item ast.Node) bool {
		switch stmt := item.(type) {
		case *ast.AssignStmt:
			if stmt.Tok == token.ASSIGN || stmt.Tok == token.DEFINE {
				for _, lhs := range stmt.Lhs {
					if id, ok := unparen(lhs).(*ast.Ident); ok {
						out[id] = true
					}
				}
			}
		case *ast.RangeStmt:
			for _, bound := range []ast.Expr{stmt.Key, stmt.Value} {
				if bound != nil {
					if id, ok := unparen(bound).(*ast.Ident); ok {
						out[id] = true
					}
				}
			}
		}
		return true
	})
	return out
}

func failureCall(node ast.Node) bool {
	found := false
	ast.Inspect(node, func(item ast.Node) bool {
		call, ok := item.(*ast.CallExpr)
		if !ok {
			return true
		}
		if selector, ok := unparen(call.Fun).(*ast.SelectorExpr); ok && failureNames[selector.Sel.Name] {
			found = true
		}
		return true
	})
	return found
}

// A def is one statement that gives a local its value: the symbols that
// statement uses, with the symbols of the definitions its operands carry.
type def struct {
	refs     refset
	pointees map[types.Object]struct{}
	unknown  bool
}

type defKey struct {
	node ast.Node
	obj  types.Object
}

type state map[types.Object]map[*def]struct{}

func (s state) clone() state {
	if s == nil {
		return nil
	}
	out := make(state, len(s))
	for obj, defs := range s {
		copied := make(map[*def]struct{}, len(defs))
		for item := range defs {
			copied[item] = struct{}{}
		}
		out[obj] = copied
	}
	return out
}

func join(first, second state) state {
	if first == nil {
		return second.clone()
	}
	if second == nil {
		return first
	}
	for obj, defs := range second {
		target := first[obj]
		if target == nil {
			target = map[*def]struct{}{}
			first[obj] = target
		}
		for item := range defs {
			target[item] = struct{}{}
		}
	}
	return first
}

func same(first, second state) bool {
	if (first == nil) != (second == nil) {
		return false
	}
	if len(first) != len(second) {
		return false
	}
	for obj, defs := range first {
		other, ok := second[obj]
		if !ok || len(other) != len(defs) {
			return false
		}
		for item := range defs {
			if _, ok := other[item]; !ok {
				return false
			}
		}
	}
	return true
}

type target struct {
	label     string
	loop      bool
	breaks    state
	continue_ state
}

type flow struct {
	a       *analyzer
	defs    map[defKey]*def
	version int
	snaps   map[*ast.IfStmt]state
	wanted  map[ast.Stmt]*ast.IfStmt
	targets []*target
	label   string
	// weak is set when the function has a goto: control flow is then not
	// read from the structure, every definition is kept and none is killed.
	weak bool
}

func newFlow(a *analyzer, checks []*ast.IfStmt) *flow {
	f := &flow{
		a:      a,
		defs:   map[defKey]*def{},
		snaps:  map[*ast.IfStmt]state{},
		wanted: map[ast.Stmt]*ast.IfStmt{},
	}
	for _, item := range checks {
		f.wanted[item] = item
	}
	return f
}

func (f *flow) run(body *ast.BlockStmt) {
	ast.Inspect(body, func(item ast.Node) bool {
		if branch, ok := item.(*ast.BranchStmt); ok && branch.Tok == token.GOTO {
			f.weak = true
		}
		return true
	})
	final := f.exec(body, state{})
	if f.weak {
		// Everything that is defined anywhere may reach every check.
		for _, check := range f.wanted {
			f.snaps[check] = final
		}
	}
}

func (f *flow) dead(s state) state {
	if f.weak {
		return s
	}
	return nil
}

func (f *flow) read(node ast.Node, s state) refset {
	out := refset{}
	if node == nil {
		return out
	}
	f.a.direct(node, out)
	written := writeTargets(node)
	ast.Inspect(node, func(item ast.Node) bool {
		if star, ok := item.(*ast.StarExpr); ok && f.readPointees(star, s, out) {
			return false
		}
		id, ok := item.(*ast.Ident)
		if !ok || written[id] {
			return true
		}
		obj := f.a.info.Uses[id]
		if f.a.local(obj) {
			for held := range s[obj] {
				out.union(held.refs)
			}
		}
		return true
	})
	return out
}

// For known local addresses, the current pointee values supersede the
// definitions that reached the expression when the address was taken.
func (f *flow) readPointees(star *ast.StarExpr, s state, into refset) bool {
	targets := f.pointees(star.X, s)
	for obj := range targets {
		for def := range s[obj] {
			into.union(def.refs)
		}
	}
	_, unknown := targets[nil]
	return len(targets) > 0 && !unknown
}

func (f *flow) setDef(s state, node ast.Node, obj types.Object, refs refset, strong bool, aliases map[types.Object]struct{}) {
	if s == nil || obj == nil || !f.a.local(obj) {
		return
	}
	key := defKey{node, obj}
	held := f.defs[key]
	if held == nil {
		held = &def{refs: refset{}}
		f.defs[key] = held
		f.version++
	}
	if held.refs.union(refs) {
		f.version++
	}
	if aliases == nil {
		if !held.unknown {
			held.unknown = true
			f.version++
		}
	} else {
		if held.pointees == nil {
			held.pointees = map[types.Object]struct{}{}
		}
		for target := range aliases {
			if _, ok := held.pointees[target]; !ok {
				held.pointees[target] = struct{}{}
				f.version++
			}
		}
	}
	if strong && !f.weak {
		s[obj] = map[*def]struct{}{held: {}}
		return
	}
	if s[obj] == nil {
		s[obj] = map[*def]struct{}{}
	}
	s[obj][held] = struct{}{}
}

func root(expr ast.Expr) *ast.Ident {
	for {
		switch item := expr.(type) {
		case *ast.Ident:
			return item
		case *ast.ParenExpr:
			expr = item.X
		case *ast.SelectorExpr:
			expr = item.X
		case *ast.IndexExpr:
			expr = item.X
		case *ast.IndexListExpr:
			expr = item.X
		case *ast.StarExpr:
			expr = item.X
		case *ast.SliceExpr:
			expr = item.X
		default:
			return nil
		}
	}
}

// pointees follows addresses of locals and copies of local pointers. A nil
// key represents a possible target beyond the ones this flow can identify.
func (f *flow) pointees(expr ast.Expr, s state) map[types.Object]struct{} {
	switch item := unparen(expr).(type) {
	case *ast.UnaryExpr:
		if id, ok := unparen(item.X).(*ast.Ident); ok && item.Op == token.AND {
			if obj := f.a.info.Uses[id]; f.a.local(obj) {
				return map[types.Object]struct{}{obj: {}}
			}
		}
	case *ast.Ident:
		obj := f.a.info.Uses[item]
		if obj == nil || obj.Type() == nil {
			return nil
		}
		if _, pointer := obj.Type().Underlying().(*types.Pointer); !pointer {
			return nil
		}
		defs := s[obj]
		if len(defs) != 0 {
			out := map[types.Object]struct{}{}
			for def := range defs {
				if def.unknown {
					out[nil] = struct{}{}
				}
				for obj := range def.pointees {
					out[obj] = struct{}{}
				}
			}
			return out
		}
	}
	return nil
}

// assign records that lhs receives a value that uses refs. Evaluate pointer
// targets in the pre-assignment state, as for the right-hand operands.
func (f *flow) assign(s, before state, node ast.Node, lhs ast.Expr, refs refset, plain bool, aliases map[types.Object]struct{}) {
	lhs = unparen(lhs)
	if id, ok := lhs.(*ast.Ident); ok {
		if id.Name == "_" {
			return
		}
		f.setDef(s, node, f.a.info.ObjectOf(id), refs, plain, aliases)
		return
	}
	if star, ok := lhs.(*ast.StarExpr); ok {
		targets := f.pointees(star.X, before)
		known := false
		for obj := range targets {
			if obj != nil {
				f.setDef(s, node, obj, refs, plain && len(targets) == 1, aliases)
				known = true
			}
		}
		if known {
			return
		}
	}
	if id := root(lhs); id != nil {
		f.setDef(s, node, f.a.info.ObjectOf(id), refs, false, nil)
	}
}

// literals records the assignments a function literal makes to locals of
// the function around it: they may happen wherever the literal is called.
func (f *flow) literals(node ast.Node, s state) {
	if node == nil || s == nil {
		return
	}
	ast.Inspect(node, func(item ast.Node) bool {
		literal, ok := item.(*ast.FuncLit)
		if !ok {
			return true
		}
		ast.Inspect(literal.Body, func(inner ast.Node) bool {
			switch stmt := inner.(type) {
			case *ast.AssignStmt:
				refs := refset{}
				for _, value := range stmt.Rhs {
					refs.union(f.read(value, s))
				}
				for _, lhs := range stmt.Lhs {
					if id := root(unparen(lhs)); id != nil {
						obj := f.a.info.ObjectOf(id)
						if obj != nil && (obj.Pos() < literal.Pos() || obj.Pos() >= literal.End()) {
							f.setDef(s, stmt, obj, refs, false, nil)
						}
					}
				}
			}
			return true
		})
		return false
	})
}

func (f *flow) execList(list []ast.Stmt, s state) state {
	for _, stmt := range list {
		s = f.exec(stmt, s)
	}
	return s
}

func (f *flow) push(loop bool) *target {
	item := &target{label: f.label, loop: loop}
	f.label = ""
	f.targets = append(f.targets, item)
	return item
}

func (f *flow) pop() {
	f.targets = f.targets[:len(f.targets)-1]
}

func (f *flow) find(label string, loop bool) *target {
	for index := len(f.targets) - 1; index >= 0; index-- {
		item := f.targets[index]
		if label != "" {
			if item.label == label {
				return item
			}
			continue
		}
		if !loop || item.loop {
			return item
		}
	}
	return nil
}

func (f *flow) exec(node ast.Stmt, s state) state {
	if s == nil {
		return nil
	}
	if check, ok := f.wanted[node]; ok {
		f.snaps[check] = s.clone()
	}
	switch stmt := node.(type) {
	case *ast.BlockStmt:
		return f.execList(stmt.List, s)
	case *ast.AssignStmt:
		for _, value := range stmt.Rhs {
			f.literals(value, s)
		}
		plain := stmt.Tok == token.ASSIGN || stmt.Tok == token.DEFINE
		var all refset
		perValue := make([]refset, len(stmt.Rhs))
		for index, value := range stmt.Rhs {
			perValue[index] = f.read(value, s)
		}
		if len(stmt.Rhs) != len(stmt.Lhs) {
			all = refset{}
			for _, refs := range perValue {
				all.union(refs)
			}
		}
		before := s
		if len(stmt.Lhs) > 1 {
			before = s.clone()
		}
		aliases := make([]map[types.Object]struct{}, len(stmt.Lhs))
		if plain && len(stmt.Rhs) == len(stmt.Lhs) {
			for index, value := range stmt.Rhs {
				aliases[index] = f.pointees(value, before)
			}
		}
		for index, lhs := range stmt.Lhs {
			refs := all
			if refs == nil {
				refs = perValue[index]
			}
			f.assign(s, before, stmt, lhs, refs, plain, aliases[index])
		}
		return s
	case *ast.DeclStmt:
		decl, ok := stmt.Decl.(*ast.GenDecl)
		if !ok {
			return s
		}
		for _, spec := range decl.Specs {
			switch item := spec.(type) {
			case *ast.ValueSpec:
				for _, value := range item.Values {
					f.literals(value, s)
				}
				for index, name := range item.Names {
					// The declared type of a variable is not a value it was
					// given: only its initial values count.
					refs := refset{}
					var aliases map[types.Object]struct{}
					if len(item.Values) == len(item.Names) {
						refs.union(f.read(item.Values[index], s))
						aliases = f.pointees(item.Values[index], s)
					} else {
						for _, value := range item.Values {
							refs.union(f.read(value, s))
						}
					}
					f.setDef(s, item, f.a.info.Defs[name], refs, true, aliases)
				}
			case *ast.TypeSpec:
				f.setDef(s, item, f.a.info.Defs[item.Name], f.read(item.Type, s), true, nil)
			}
		}
		return s
	case *ast.ExprStmt:
		f.literals(stmt.X, s)
		if call, ok := unparen(stmt.X).(*ast.CallExpr); ok {
			if id, ok := unparen(call.Fun).(*ast.Ident); ok && id.Name == "panic" {
				if _, builtin := f.a.info.Uses[id].(*types.Builtin); builtin {
					return f.dead(s)
				}
			}
			if f.a.terminates(call) {
				return f.dead(s)
			}
		}
		return s
	case *ast.GoStmt:
		f.literals(stmt.Call, s)
		return s
	case *ast.DeferStmt:
		f.literals(stmt.Call, s)
		return s
	case *ast.SendStmt:
		f.literals(stmt, s)
		return s
	case *ast.ReturnStmt:
		for _, value := range stmt.Results {
			f.literals(value, s)
		}
		return f.dead(s)
	case *ast.BranchStmt:
		label := ""
		if stmt.Label != nil {
			label = stmt.Label.Name
		}
		switch stmt.Tok {
		case token.BREAK:
			if item := f.find(label, false); item != nil {
				item.breaks = join(item.breaks, s)
			}
			return f.dead(s)
		case token.CONTINUE:
			if item := f.find(label, true); item != nil {
				item.continue_ = join(item.continue_, s)
			}
			return f.dead(s)
		}
		return s
	case *ast.LabeledStmt:
		f.label = stmt.Label.Name
		out := f.exec(stmt.Stmt, s)
		f.label = ""
		return out
	case *ast.IfStmt:
		if stmt.Init != nil {
			s = f.exec(stmt.Init, s)
			if s == nil {
				return nil
			}
		}
		f.literals(stmt.Cond, s)
		thenS := f.exec(stmt.Body, s.clone())
		elseS := s
		if stmt.Else != nil {
			elseS = f.exec(stmt.Else, s.clone())
		}
		return join(thenS, elseS)
	case *ast.ForStmt:
		return f.loop(stmt, stmt.Init, stmt.Cond, stmt.Post, nil, stmt.Body, s)
	case *ast.RangeStmt:
		return f.loop(stmt, nil, nil, nil, stmt, stmt.Body, s)
	case *ast.SwitchStmt:
		if stmt.Init != nil {
			s = f.exec(stmt.Init, s)
			if s == nil {
				return nil
			}
		}
		f.literals(stmt.Tag, s)
		return f.clauses(stmt.Body, s, nil)
	case *ast.TypeSwitchStmt:
		if stmt.Init != nil {
			s = f.exec(stmt.Init, s)
			if s == nil {
				return nil
			}
		}
		var guard ast.Expr
		switch assign := stmt.Assign.(type) {
		case *ast.AssignStmt:
			guard = assign.Rhs[0]
		case *ast.ExprStmt:
			guard = assign.X
		}
		refs := f.read(guard, s)
		return f.clauses(stmt.Body, s, refs)
	case *ast.SelectStmt:
		item := f.push(false)
		var out state
		for _, clause := range stmt.Body.List {
			comm := clause.(*ast.CommClause)
			in := s.clone()
			if comm.Comm != nil {
				in = f.exec(comm.Comm, in)
			}
			out = join(out, f.execList(comm.Body, in))
		}
		out = join(out, item.breaks)
		f.pop()
		if out == nil && f.weak {
			return s
		}
		return out
	}
	return s
}

// terminates reports a call that does not return: a test that is failed or
// skipped stops at once, as does os.Exit and runtime.Goexit.
func (a *analyzer) terminates(call *ast.CallExpr) bool {
	selector, ok := unparen(call.Fun).(*ast.SelectorExpr)
	if !ok {
		return false
	}
	fn, ok := a.info.Uses[selector.Sel].(*types.Func)
	if !ok || fn.Pkg() == nil {
		return false
	}
	switch fn.Pkg().Path() {
	case "testing":
		switch fn.Name() {
		case "Fatal", "Fatalf", "FailNow", "Skip", "Skipf", "SkipNow":
			return true
		}
	case "os":
		return fn.Name() == "Exit"
	case "runtime":
		return fn.Name() == "Goexit"
	}
	return false
}

// clauses runs the case clauses of a switch. For a type switch, refs are the
// symbols of the switched value, which the clause binding carries.
func (f *flow) clauses(body *ast.BlockStmt, s state, refs refset) state {
	item := f.push(false)
	var out, carry state
	hasDefault := false
	for _, clause := range body.List {
		cc := clause.(*ast.CaseClause)
		in := s.clone()
		if carry != nil {
			in = join(in, carry)
			carry = nil
		}
		for _, expr := range cc.List {
			f.literals(expr, in)
		}
		if refs != nil {
			f.setDef(in, cc, f.a.info.Implicits[cc], refs, true, nil)
		}
		end := f.execList(cc.Body, in)
		if cc.List == nil {
			hasDefault = true
		}
		if len(cc.Body) > 0 {
			if branch, ok := cc.Body[len(cc.Body)-1].(*ast.BranchStmt); ok && branch.Tok == token.FALLTHROUGH {
				carry = end
				continue
			}
		}
		out = join(out, end)
	}
	if !hasDefault {
		out = join(out, s)
	}
	out = join(out, item.breaks)
	f.pop()
	return out
}

// loop runs a for or a range statement until the state at its head is stable.
func (f *flow) loop(node ast.Stmt, init ast.Stmt, cond ast.Expr, post ast.Stmt, rng *ast.RangeStmt, body *ast.BlockStmt, s state) state {
	if init != nil {
		s = f.exec(init, s)
		if s == nil {
			return nil
		}
	}
	label := f.label
	f.label = ""
	head := s.clone()
	var exit state
	for round := 0; round < 64; round++ {
		before := f.version
		f.label = label
		item := f.push(true)
		in := head.clone()
		if cond != nil {
			f.literals(cond, in)
		}
		if rng != nil {
			refs := f.read(rng.X, in)
			for _, bound := range []ast.Expr{rng.Key, rng.Value} {
				if bound != nil {
					f.assign(in, in, rng, bound, refs, rng.Tok == token.DEFINE || rng.Tok == token.ASSIGN, nil)
				}
			}
		}
		end := f.exec(body, in)
		cont := join(end, item.continue_)
		if post != nil && cont != nil {
			cont = f.exec(post, cont)
		}
		next := join(head.clone(), cont)
		exit = item.breaks
		f.pop()
		stable := same(next, head) && f.version == before
		head = next
		if stable {
			break
		}
	}
	if cond != nil || rng != nil || f.weak {
		exit = join(exit, head)
	}
	return exit
}
