using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using ChatWithYourBusinessRules.Contracts;
using ChatWithYourBusinessRules.Repositories;

var host = new HostBuilder()
    .ConfigureFunctionsWebApplication()
    .ConfigureServices(services => {
        services.AddApplicationInsightsTelemetryWorkerService();
        services.ConfigureFunctionsApplicationInsights();
        services.AddTransient<IDatabaseRulesRepository, DatabaseRulesRespository>();
    })
    .Build();

host.Run();
