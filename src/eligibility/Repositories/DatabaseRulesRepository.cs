using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Data.SqlClient;

using Polly;
using ChatWithYourBusinessRules.Contracts;
using ChatWithYourBusinessRules.Models;


namespace ChatWithYourBusinessRules.Repositories;

public class DatabaseRulesRespository : IDatabaseRulesRepository
{
    public DatabaseRulesRespository(
        ILogger<DatabaseRulesRespository> logger)
    {
        _logger = logger;
    }

    public async Task<IEnumerable<DatabaseRule>> GetRulesAsync(string workflowName)
    {
        var databaseRules = new List<DatabaseRule>();
        var policy = Policy.Handle<SqlException>()
            .WaitAndRetryAsync(5, retryAttempt => TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)), (exception, timeSpan, retryCount, context) =>
            {
                _logger.LogError(exception, "Error getting rules from database. Retrying...");
            });

        var connectionString = Environment.GetEnvironmentVariable("RulesDataConnectionString");
        var sqlCommandText = "SELECT [RuleName], [Properties], [Operator], [ErrorMessage], [Enabled], [RuleExpressionType], [Expression], [Actions], [SuccessEvent], [RuleNameFK], [WorkflowName] FROM [dbo].[Rules] WHERE [WorkflowName] LIKE @WorkflowName";

        try
        {    
            await policy.ExecuteAsync(async () => 
            {
                using var connection = new SqlConnection(connectionString);
                await connection.OpenAsync();
                
                using var command = new SqlCommand(sqlCommandText, connection);
                command.Parameters.AddWithValue("@WorkflowName", workflowName);

                var reader = await command.ExecuteReaderAsync();
                while (await reader.ReadAsync())
                {
                    databaseRules.Add(new DatabaseRule(
                        reader.GetString(0),
                        GetStringOrDefault(reader, 1),
                        GetStringOrDefault(reader, 2),
                        GetStringOrDefault(reader, 3),
                        reader.GetBoolean(4),
                        reader.GetInt32(5),
                        GetStringOrDefault(reader, 6),
                        GetStringOrDefault(reader, 7),
                        GetStringOrDefault(reader, 8),
                        GetStringOrDefault(reader, 9),
                        GetStringOrDefault(reader, 10)
                    ));
                }
            });
        }
        catch(Exception ex)
        {
            _logger.LogError(ex, "Error getting rules from database.");
            throw;
        }

        return databaseRules;
    }

    private string GetStringOrDefault(SqlDataReader reader, int columnIndex)
    {
        return reader.IsDBNull(columnIndex) ? null : reader.GetString(columnIndex);
    }

    private ILogger<DatabaseRulesRespository> _logger;
}