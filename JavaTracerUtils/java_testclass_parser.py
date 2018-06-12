"""
A static parser for a java test class
"""
import plyj.parser as plyj
import plyj.model as model

class JavaTestClassFileParser(object):
    parser = plyj.Parser()

    @classmethod
    def parse_and_return_methodnameTannotations(cls, java_test_file_path):
        with open(java_test_file_path, 'r') as tfile:
            tree = cls.parser.parse_file(tfile)
            for type_decl in tree.type_declarations:
                methodnameTannotations = []  # (method_name, ['Test', 'Deprecated'])
                for method_decl in [decl for decl in type_decl.body if type(decl) is model.MethodDeclaration]:
                    annotations = []
                    for modifier in method_decl.modifiers:
                        if type(modifier) is model.Annotation:
                            annotations.append(modifier.name.value)
                    methodnameTannotations.append((method_decl.name, annotations))
        return methodnameTannotations