using System.Diagnostics;
using RulesEngine.Models;

namespace ChatWithYourBusinessRules.Models;

public static class RuleConverter
{
    public static List<Rule> ConvertToRules(IList<DatabaseRule> databaseRules)
    {
        var ruleDictionary = new Dictionary<string, Rule>();
        var results = new List<Rule>();

        foreach(var databaseRule in databaseRules)
        {
            if (string.IsNullOrEmpty(databaseRule.RuleName)) throw new ApplicationException("RuleName is required.");
            if (string.IsNullOrEmpty(databaseRule.Operator))
            {
                if (string.IsNullOrEmpty(databaseRule.Expression)) throw new ApplicationException("Operator is required if expression is null or empty.");
            } 
            else
            {
                if (!string.IsNullOrEmpty(databaseRule.Expression)) throw new ApplicationException("Operator must be null if expression is not null or empty.");
            }

            var rule = new Rule
            {
                RuleName = databaseRule.RuleName,
                Operator = databaseRule.Operator,
                Expression = databaseRule.Expression,
                Rules = new List<Rule>()
            };
            ruleDictionary[databaseRule.RuleName] = rule;
        }

        foreach(var databaseRule in databaseRules)
        {
            if (!string.IsNullOrEmpty(databaseRule.RuleNameFK))
            {
                var parentRule = ruleDictionary[databaseRule.RuleNameFK];
                var childRule = ruleDictionary[databaseRule.RuleName];
                ((List<Rule>)parentRule.Rules).Add(childRule);
            }
        }

        foreach(var rule in ruleDictionary.Values)
        {
            if (!databaseRules.Any(dr => dr.RuleName == rule.RuleName && !string.IsNullOrEmpty(dr.RuleNameFK)))
            {
                results.Add(rule);
            }
        }

        return results;
    }
}
