# use clang to load and walk a compilation database
import textwrap

from more_itertools import last
from typing_extensions import Iterable

from renaissance.impl.clang import ClangASTNode, CPPPatternFactory
from renaissance.impl.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.impl.types import Constructor, Method, TypeReference
from renaissance.syntax_tree import (
    ASTRefactorActions,
    RecipeASTProcessor,
    recipe_step,
)
from renaissance.syntax_tree import ASTProcessor, ASTNode, TextUtils, ASTFactory
from renaissance.syntax_tree.ast_finder import matches_kind

example_1 = textwrap.dedent("""
#include <vector>
struct Size
{
    double length;
    double width;

    // Constructor to initialize the Rectangle object with length and width
    Size() : length(0), width(0) {}
    Size(double len, double wid) : length(len), width(wid) {}

    Size size()
    {
        return Size(this->length, this->width);
    }
};

typedef const char* string;

int main(){
    // do nothing
}
void setItemLayout(int, Size size){
}
class aClass{
    void main1(std::vector<int> m_items){
        std::vector<int> idToBeReplaced;
        idToBeReplaced.push_back((int)m_items.size());
        setItemLayout(1, Size(this->getBounds().size().width, 30));
    }
    Size getBounds(){
        return Size(10, 30);
    }
};

class ListView_LEGACY{
    public:
        ListView_LEGACY();
        ListView_LEGACY(string container, int val);
        Size size;
};

ListView_LEGACY::ListView_LEGACY(string container, int val){

}
ListView_LEGACY::ListView_LEGACY(){

}

class derived : public ListView_LEGACY{
    public:
        derived(string cont) : ListView_LEGACY(cont, 5) {
                                // something
                            };
        void another_func(int s);
};

void derived::another_func(int s){
    int a = 0;
    // another_func 0
    // another_func 1
}
                         
void main2(string container){
    /* hahaha*/
    ListView_LEGACY listview(container, 3);
    int b;
    int a;
    listview.size = Size(4, 5);
}

void main3()
{
    int b;
    string container, foo;
    ListView_LEGACY listview(container, 3);
    derived d(foo);
    listview.size = Size(4, 5);
}

void main4(std::vector<int> m_items)
{
    /**
     * multi-line comments
     * in my code;
     * do this wrack my indent algo?
     */
    std::vector<int> idToBeReplaced;
    /**
     * multi-line comments
     * in my code;
     * do this wrack my indent algo?
     */
    idToBeReplaced.push_back((int)m_items.size());
    /**
     * multi-line comments
     * in my code;
     * do this wrack my indent algo?
     */
}
""")
expected_output = textwrap.dedent("""
                                         void main(){
    std::vector<int> NEW_ID;
    NEW_ID.push_back((int)m_items.size());
    setItemLayout(1, Size(this->getBounds().size().width,30));
}

void main() {
    /*ahah*/
    ListViewCustom listview;
    ListViewHeader listviewHeader0
    /* Conversion note: give header appropriate name */
    ListViewHeader listviewHeader1
    /* Conversion note: give header appropriate name */
    ListViewHeader listviewHeader2 /* Conversion note: give header appropriate name */
    bool b; bool a;
    listview(container),
    listviewHeader0(listview),
    listviewHeader1(listview),
    listviewHeader2(listview);
    listview.size = Size(4, 5);
    listviewHeader0.name = L"listviewHeader0";/* Conversion note: give header appropriate name */
    listviewHeader0.size = Size(256, 30); /* Conversion note: provide correct sizes */
    listviewHeader1.name = L"listviewHeader1";/* Conversion note: give header appropriate name */
    listviewHeader1.size = Size(256, 30); /* Conversion note: provide correct sizes */
    listviewHeader2.name = L"listviewHeader2";/* Conversion note: give header appropriate name */
    listviewHeader2.size = Size(256, 30); /* Conversion note: provide correct sizes */
}

class ListView_LEGACY {
        ListView_LEGACY(string container, int val);
};
class derived: public ListView_LEGACY {
        derived(string cont):ListViewCustom(cont), m_headers {,
                                 std:make_unique<ListViewHeader>(*this),
                                 std:make_unique<ListViewHeader>(*this),
                                 std:make_unique<ListViewHeader>(*this),
                                 std:make_unique<ListViewHeader>(*this),
                                 std:make_unique<ListViewHeader>(*this)}{
            //something
        };
        void another_func(int s );
};
void __REPLACEMENT__(){}

void main(){
        ListViewCustom listview;
        ListViewHeader listviewHeader0
        /* Conversion note: give header appropriate name */
        ListViewHeader listviewHeader1
        /* Conversion note: give header appropriate name */
        ListViewHeader listviewHeader2 /* Conversion note: give header appropriate name */
        bool b;
        string container;
        listview(container),
        listviewHeader0(listview),
        listviewHeader1(listview),
        listviewHeader2(listview);
        derived d();
        listview.size = Size(4, 5);
        listviewHeader0.name = L"listviewHeader0";/* Conversion note: give header appropriate name */
        listviewHeader0.size = Size(256, 30); /* Conversion note: provide correct sizes */
        listviewHeader1.name = L"listviewHeader1";/* Conversion note: give header appropriate name */
        listviewHeader1.size = Size(256, 30); /* Conversion note: provide correct sizes */
        listviewHeader2.name = L"listviewHeader2";/* Conversion note: give header appropriate name */
        listviewHeader2.size = Size(256, 30); /* Conversion note: provide correct sizes */
}

void main(){
    /**
    * multi-line comments
    * in my code;
    * do this wrack my indent algo?
    */
    std::vector<int> NEW_ID;
                                /**
    * multi-line comments
    * in my code;
    * do this wrack my indent algo?
    */
    NEW_ID.push_back((int)m_items.size());
                                /**
    * multi-line comments
    * in my code;
    * do this wrack my indent algo?
    */
}
""")


# generate a simple code base provider in real life use a compilation database
def simple_codebase_provider() -> Iterable[tuple[ASTFactory, ASTNode]]:
    for impl_type in [ClangASTNode, ClangJsonASTNode][0:1]:
        factory = ASTFactory(impl_type)
        atu1 = factory.create_from_text(example_1, impl_type.__name__ + "1.cpp")
        yield factory, atu1


class MyRefactor:
    def __init__(self):
        self._calls = []

    @recipe_step(order=0)
    def recipe(self, ast_processor: ASTProcessor):
        pattern = CPPPatternFactory(ast_processor.factory)
        actions = ASTRefactorActions(ast_processor, pattern)
        actions.replace_text("ListView_LEGACY", "ListViewCustom", skip_kind=TypeReference)
        actions.replace_name("another_func", "__REPLACEMENT__", Method)
        actions.replace_text("idToBeReplaced", "NEW_ID")
        # TODO debate the way to replace this the options are:
        # 1. make a match of the consecutive nodes.
        # 2. find a neat construction for the current backtick replacement
        actions.replace_declaration("int $var;", r"bool $var`int\s+(.+)`;")
        # create a constructor pattern
        constructor_pattern = pattern.create(
            "typedef int string; class ListView_LEGACY { ListView_LEGACY(string container, int val); };",
            kind="Constructor",
        )
        # create a pattern to match a call to a constructor in both declarations and derived classes
        constructor_call_pattern = pattern.create_constructor_call("$var($container, $headerCount)")
        # search for the constructor pattern
        for constructor_match in ast_processor.find_match(constructor_pattern):
            # and then search for the referenced by calls to the constructor
            for constructor_call in constructor_match.match_referenced_by([constructor_call_pattern]):
                var_node = constructor_call.nodes["$var"][0]
                parent = var_node.parent
                assert isinstance(parent, ASTNode), f"{parent} is not an ASTNode"
                header_count = int(constructor_call.expansions["$headerCount"])
                # remove the count argument from the constructor call
                # TODO it would be a lot easier if ast rewrite would support removal of the second argument
                # but currently (I guess) that would lead to a dangling comma
                # TODO the items between the backtick represent a regex where all groups are the used replacements
                # this might need some investigation what is the best way to handle this
                if matches_kind(parent, Constructor):
                    # remove constructor header count argument
                    ast_processor.replace(r"ListViewCustom($container)", constructor_call)
                    repl = ",\n    ".join("std:make_unique<ListViewHeader>(*this)" for _ in range(header_count))
                    ast_processor.insert_after(", m_headers {" + repl + "}", constructor_call, True, False)
                else:
                    var = parent.name
                    container = constructor_call.expansions["$container"]
                    # replace the constructor call with a ListViewCustom object
                    ast_processor.replace(f"ListViewCustom {var}({container});", parent)
                    # find reference to the declaration
                    size_match = last(ref.node.get_ancestor("Call_?Expr") for ref in parent.referenced_by)

                    for h in range(header_count):
                        ast_processor.insert_after(
                            f"\n/* Conversion note: give header appropriate name */\nListViewHeader listviewHeader{h}({var});",
                            parent,
                            True,
                            False,
                        )
                        if size_match:
                            text = TextUtils.strip_indent(f"""
                                listviewHeader{h}.name = L"listviewHeader{h}";/* Conversion note: give header appropriate name */
                                listviewHeader{h}.size = Size(256, 30); /* Conversion note: provide correct sizes */
                                """)
                            ast_processor.insert_after(text, size_match, True, False)
        # for idx, line in  enumerate(ast_processor.apply_to_string().split('\n')):
        #     print(f'{idx+1}: {line}')
        TextUtils.to_clipboard(ast_processor.apply_to_string())


def batch_recipe_example():
    print("example batch analysis using recipe:\n")
    recipe_ast_processor = RecipeASTProcessor(MyRefactor(), simple_codebase_provider, r".*", in_memory=True)
    recipe_ast_processor.run()


if __name__ == "__main__":
    batch_recipe_example()
