CREATE TABLE [dbo].[enhancedProductMapping](
        [name] [nvarchar](150) NULL,
        [id] [bigint] NOT NULL,
        [state] [nvarchar](50) NOT NULL,
        [value] [nvarchar](950) NOT NULL,
CONSTRAINT [PK_enhancedProductMapping] PRIMARY KEY
(
	[id] ASC
)
) ON [PRIMARY]
