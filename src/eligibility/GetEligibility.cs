using System.Text.Json;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using RulesEngine.Models;
using ChatWithYourBusinessRules.Contracts;
using ChatWithYourBusinessRules.Models;

namespace ChatWithYourBusinessRules;

public class GetEligibility
{
    private readonly ILogger<GetEligibility> _logger;

    private readonly IDatabaseRulesRepository _databaseRulesRepository;

    public GetEligibility(
        ILogger<GetEligibility> logger,
        IDatabaseRulesRepository databaseRulesRepository)
    {
        _logger = logger;
        _databaseRulesRepository = databaseRulesRepository;
    }

    [Function("GetEligibility")]
    public async Task<IActionResult> Run(
        [HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequest req)
    {
        _logger.LogInformation("C# HTTP trigger function processed a request.");
        var results = new Dictionary<string, bool>();

        try
        {
            using var reader = new StreamReader(req.Body);
            var body = await reader.ReadToEndAsync();
            var attributes = JsonSerializer.Deserialize<List<string>>(body);
            if (attributes == null)
            {
                return new BadRequestObjectResult("Inavlid input; expected a list of attributes.");
            }

            var databaseRules = await _databaseRulesRepository.GetRulesAsync("Eligibility");
            var rules = RuleConverter.ConvertToRules(databaseRules.ToList());
            var workflow = new Workflow
            {
                WorkflowName = "Eligibility",
                Rules = rules
            };

            var engine = new RulesEngine.RulesEngine(new[] { workflow });
            var engineResults = await engine.ExecuteAllRulesAsync("Eligibility", attributes);
            foreach (var result in engineResults)
            {
                results[result.Rule.RuleName] = result.IsSuccess;
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting eligibility");
            return new StatusCodeResult(StatusCodes.Status500InternalServerError);
        }

        return new OkObjectResult(results);
    }
}