/****** Object:  Table [dbo].[ScopedParam]    Script Date: 6/5/2024 1:58:34 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[ScopedParam](
	[Name] [nvarchar](450) NOT NULL,
	[Expression] [nvarchar](max) NULL,
	[RuleName] [nvarchar](450) NULL,
	[WorkflowName] [nvarchar](450) NULL,
 CONSTRAINT [PK_ScopedParam] PRIMARY KEY CLUSTERED 
(
	[Name] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[ScopedParam]  WITH CHECK ADD  CONSTRAINT [FK_ScopedParam_Rules_RuleName] FOREIGN KEY([RuleName])
REFERENCES [dbo].[Rules] ([RuleName])
GO

ALTER TABLE [dbo].[ScopedParam] CHECK CONSTRAINT [FK_ScopedParam_Rules_RuleName]
GO

ALTER TABLE [dbo].[ScopedParam]  WITH CHECK ADD  CONSTRAINT [FK_ScopedParam_Workflows_WorkflowName] FOREIGN KEY([WorkflowName])
REFERENCES [dbo].[Workflows] ([WorkflowName])
GO

ALTER TABLE [dbo].[ScopedParam] CHECK CONSTRAINT [FK_ScopedParam_Workflows_WorkflowName]
GO


