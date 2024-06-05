CREATE TABLE [dbo].[productMapping](
	[name] [nvarchar](150) NULL,
	[id] [bigint] NOT NULL,
	[state] [nvarchar](50) NOT NULL,
	[value] [nvarchar](950) NOT NULL,
CONSTRAINT [PK_productMapping] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]