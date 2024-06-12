import json, re, uuid

class Rule:
    def __init__(self, value = None, left = None, right = None):
        self.name = None
        self.value = value
        self.left = left
        self.right = right

    def __is_operator__(self, value):
        if value in ["AND", "OR"]:
            return True
        else:
            return False
        
    def to_dict(self):
        rules = None

        if self.left is not None: 
            if rules is None:
                rules = []
            rules.append(self.left.to_dict())
        
        if self.right is not None:
            if rules is None:
                rules = []
            rules.append(self.right.to_dict())

        if self.__is_operator__(self.value):
            expression = None
            if self.value.upper() == "AND":
                operator = "And"
            else:
                operator = "Or"
        else:
            operator = None
            if self.value.startswith("NOT "):
                value = self.value[4:]
                value = value.strip('\'"')
                expression = f'!input1.Contains(\"{value}\")'
            else:
                value = self.value.strip('\'"')
                expression = f'input1.Contains(\"{value}\")'
        return {
            "RuleName": self.name if self.name else str(uuid.uuid4()),
            "Expression": expression, 
            "Operator": operator,
            "Rules": rules
        } 
    
    @staticmethod
    def parse_expression(expression):
        def tokenize(expr):
            return re.findall(r'"[^"]*"|NOT\s+(?:[0-9]+|"[^"]+")|\(|\)|AND|OR|\b[^ )(]+', expression)

        def precedence(op):
            precedences = {"AND": 2, "OR": 1}
            return precedences.get(op, 0)

        def to_postfix(tokens):
            stack = []
            postfix = []
            for token in tokens:
                if token in ["AND", "OR"]:
                    while (stack and precedence(stack[-1]) >= precedence(token)):
                        postfix.append(stack.pop())
                    stack.append(token)
                elif token == "(":
                    stack.append(token)
                elif token == ")":
                    while stack and stack[-1] != "(":
                        postfix.append(stack.pop())
                    stack.pop()  # Pop '('
                else:
                    postfix.append(token)
            while stack:
                postfix.append(stack.pop())
            return postfix

        def build_tree(postfix):
            stack = []
            for token in postfix:
                if token in ["AND", "OR"]:
                    right = stack.pop()
                    left = stack.pop()
                    stack.append(Rule(token, left, right))
                else:
                    stack.append(Rule(token))
            return stack[0]

        tokens = tokenize(expression)
        postfix = to_postfix(tokens)
        return build_tree(postfix)

    @staticmethod      
    def rule_serializer(obj):
        if isinstance(obj, Rule):
            return obj.to_dict()
        raise TypeError("Unsupported type")

################################################################################
expression = "(((ABC26 AND DEF50 AND (97GHI OR 80JKL OR 97418 OR 97422 OR 97430 OR 97564 OR 97640 OR 97632 OR 97536)) OR (((97028 OR 97029 OR 97170 OR 97172) AND (NOT 97180)) AND (97546 OR 97610 OR 97644 OR 97814 OR 97444 OR 97550 OR 97386)) OR ((97344 OR 97346) AND (97418 OR 97422 OR 97430 OR 97632 OR 97546 OR 97564))) AND (NOT 82118) AND (NOT 103086))"
expression = "(((97126 AND 97350 AND (97838 OR 80118 OR 97418 OR 97422 OR 97430 OR 97564 OR 97640 OR 97632 OR 97536)) OR (((97028 OR 97029 OR 97170 OR 97172) AND (NOT 97180)) AND (97546 OR 97610 OR 97644 OR 97814 OR 97444 OR 97550 OR 97386)) OR ((97344 OR 97346) AND (97418 OR 97422 OR 97430 OR 97632 OR 97546 OR 97564))) AND (NOT 82118) AND (NOT 103086))"
root = Rule.parse_expression(expression)
with open('output.json', 'w') as f:
    f.write(json.dumps(root, default=Rule.rule_serializer, indent=4))

print("Done!")