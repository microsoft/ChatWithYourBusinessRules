/****** Object:  Table [dbo].[Rules]    Script Date: 6/5/2024 1:57:50 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[Rules](
	[RuleName] [nvarchar](450) NOT NULL,
	[Properties] [nvarchar](max) NULL,
	[Operator] [nvarchar](max) NULL,
	[ErrorMessage] [nvarchar](max) NULL,
	[Enabled] [bit] NOT NULL,
	[RuleExpressionType] [int] NOT NULL,
	[Expression] [nvarchar](max) NULL,
	[Actions] [nvarchar](max) NULL,
	[SuccessEvent] [nvarchar](max) NULL,
	[RuleNameFK] [nvarchar](450) NULL,
	[WorkflowName] [nvarchar](450) NULL,
 CONSTRAINT [PK_Rules] PRIMARY KEY CLUSTERED 
(
	[RuleName] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[Rules]  WITH CHECK ADD  CONSTRAINT [FK_Rules_Rules_RuleNameFK] FOREIGN KEY([RuleNameFK])
REFERENCES [dbo].[Rules] ([RuleName])
GO

ALTER TABLE [dbo].[Rules] CHECK CONSTRAINT [FK_Rules_Rules_RuleNameFK]
GO

ALTER TABLE [dbo].[Rules]  WITH CHECK ADD  CONSTRAINT [FK_Rules_Workflows_WorkflowName] FOREIGN KEY([WorkflowName])
REFERENCES [dbo].[Workflows] ([WorkflowName])
GO

ALTER TABLE [dbo].[Rules] CHECK CONSTRAINT [FK_Rules_Workflows_WorkflowName]
GO


