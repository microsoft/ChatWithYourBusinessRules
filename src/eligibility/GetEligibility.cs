using System.Configuration;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.Functions.Worker.Extensions.Sql;
using Microsoft.Extensions.Logging;
using RulesEngine.Models;
using System.Text;
using System.Text.Json;

namespace ChatWithYourBusinessRules;

public class GetEligibility
{
    private readonly ILogger<GetEligibility> _logger;

    public GetEligibility(ILogger<GetEligibility> logger)
    {
        _logger = logger;
    }

    [Function("GetEligibility")]
    public async Task<IActionResult> Run(
        [HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequest req,
        [SqlInput(
            "SELECT [RuleName], [Properties], [Operator], [ErrorMessage], [Enabled], [RuleExpressionType], [Expression], [Actions], [SuccessEvent], [RuleNameFK], [WorkflowName] FROM [dbo].[Rules] WHERE [WorkflowName] LIKE 'Eligibility'",
            "RulesDataConnectionString"
        )] IEnumerable<DatabaseRule> databaseRules)
    {
        _logger.LogInformation("C# HTTP trigger function processed a request.");
        
        using var reader = new StreamReader(req.Body);
        var requestBody = await reader.ReadToEndAsync();
        List<string>? input = JsonSerializer.Deserialize<List<string>>(requestBody);
        if (input == null) return new BadRequestObjectResult("Please provide a list of strings in the request body");

        var rules = GetRules(databaseRules);
        var workflow = new Workflow
        {
            WorkflowName = "Eligibility",
            Rules = rules
        };

        var engine = new RulesEngine.RulesEngine(new[] { workflow });
        var results = await engine.ExecuteAllRulesAsync("Eligibility", input);
        var eligibilities = new Dictionary<string, bool>();
        foreach (var result in results)
        {
            eligibilities[result.Rule.RuleName] = result.IsSuccess;
        }

        return new OkObjectResult(eligibilities);
    }

    private static List<Rule> GetRules(IEnumerable<DatabaseRule> databaseRules)
    {
        var ruleDictionary = new Dictionary<string, Rule>();
        var rootRules = new List<Rule>();

        foreach (var databaseRule in databaseRules)
        {
            var rule = new Rule
            {
                RuleName = databaseRule.RuleName,
                Operator = databaseRule.Operator,
                Expression = databaseRule.Expression,
                Rules = new List<Rule>()
            };

            ruleDictionary[databaseRule.RuleName] = rule;
        }

        foreach (var databaseRule in databaseRules)
        {
            if (!string.IsNullOrEmpty(databaseRule.RuleNameFK))
            {
                var parentRule = ruleDictionary[databaseRule.RuleNameFK];
                var childRule = ruleDictionary[databaseRule.RuleName];
                ((List<Rule>)parentRule.Rules).Add(childRule);
            }
        }

        foreach (var rule in ruleDictionary.Values)
        {
            if (!databaseRules.Any(dr => dr.RuleName == rule.RuleName && !string.IsNullOrEmpty(dr.RuleNameFK)))
            {
                rootRules.Add(rule);
            }
        }

        return rootRules;
    }
}