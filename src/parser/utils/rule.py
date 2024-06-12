import re, uuid

class Rule:
    def __init__(self, name=None, value=None, left=None, right=None, enabled = True, expression_type = 0):
        self.name = name
        self.value = value
        self.left = left
        self.right = right
        self.enabled = enabled
        self.expression_type = expression_type

    def __is_operator__(self, val):
        if val and val.upper() in ["AND", "OR"]:
            return True
        else:
            return False
        
    def get_table(self, workflow_name = "Eligibilty"):
        table = []

        def traverse(node, parent_name):
            if node is None:
                return
            
            node.name = node.name if node.name else str(uuid.uuid4())
            if (node.__is_operator__(node.value)):
                expression = None
                operator = "And" if node.value.upper() == "AND" else "Or"
            else:
                if node.value.upper().startswith("NOT "):
                    expression = f'!input1.Contains("{node.value[4:].strip()}")'
                else:
                    expression = f'input1.Contains("{node.value.strip()}")'
                operator = None

            row = {
                "RuleName": node.name,
                "Operator": operator,
                "Enabled": node.enabled,
                "RuleExpressionType": node.expression_type,
                "Expression": expression,
                "RuleNameFK": parent_name,
                "WorkflowName": workflow_name
            }

            table.append(row)
            traverse(node.left, node.name)
            traverse(node.right, node.name)

        traverse(self, None)
        return table

    @staticmethod
    def parse_expression(expression):
        def tokenize(param):
            return re.findall(r'"[^"]*"|NOT\s+(?:[0-9]+|"[^"]+")|\(|\)|AND|OR|\b[^ )(]+', param)
        
        def precedence(op):
            precedences = {"AND": 2, "OR": 1} 
            return precedences.get(op.upper(), 0)
        
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
                    stack.append(Rule(value=token, left=left, right=right))
                else:
                    stack.append(Rule(value=token))
            return stack[0]

        tokens = tokenize(expression)
        postfix = to_postfix(tokens)
        return build_tree(postfix)
