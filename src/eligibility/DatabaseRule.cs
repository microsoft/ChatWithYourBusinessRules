namespace ChatWithYourBusinessRules;
public record DatabaseRule(
    string RuleName,
    string Properties,
    string Operator,
    string ErrorMessage,
    bool Enabled,
    int RuleExpressionType,
    string Expression,
    string Actions,
    string SuccessEvent,
    string RuleNameFK,
    string WorkflowName
);