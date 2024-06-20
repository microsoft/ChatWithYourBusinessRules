using ChatWithYourBusinessRules.Models;

namespace ChatWithYourBusinessRules.Contracts;

public interface IDatabaseRulesRepository
{
    Task<IEnumerable<DatabaseRule>> GetRulesAsync(string workflowName);
}