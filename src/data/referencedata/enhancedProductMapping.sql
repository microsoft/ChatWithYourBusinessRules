CREATE TABLE [dbo].[enhancedProductMapping](
        [name] [nvarchar](150) NULL,
        [id] [bigint] NOT NULL,
        [state] [nvarchar](50) NOT NULL,
        [value] [nvarchar](950) NOT NULL,
	[enhanced_value] [nvarchar](MAX) NULL,
	[translated_value] [nvarchar](MAX) NULL,
	[cat1_codes] [nvarchar](MAX) NULL,
	[cat2_codes] [nvarchar](MAX) NULL,
	[cat3_codes] [nvarchar](MAX) NULL
CONSTRAINT [PK_enhancedProductMapping] PRIMARY KEY
(
	[id] ASC
)
) ON [PRIMARY]
