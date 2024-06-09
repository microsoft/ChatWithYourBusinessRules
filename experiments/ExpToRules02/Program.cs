using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using RulesEngine;
using RulesEngine.Models;

JsonSerializerOptions options = new JsonSerializerOptions {
    Converters = { new JsonStringEnumConverter(JsonNamingPolicy.CamelCase) }
};

using var reader = File.OpenText("output.json");
var rule = JsonSerializer.Deserialize<Rule>(reader.ReadToEnd(), options);

var workflow = new Workflow();
workflow.WorkflowName = "Test";
workflow.Rules = new [] { rule };

var engine = new RulesEngine.RulesEngine(new[] { workflow });

//var test = new List<string> {"97126", "97350", "97838", "103086"};
var test = new List<string> {"97126", "97350", "97838"};

var results = await engine.ExecuteAllRulesAsync("Test", test);
foreach (var result in results)
{
    Console.WriteLine($"Result: {result.Rule.RuleName} - {result.IsSuccess}");
}