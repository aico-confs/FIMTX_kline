from model import InvestDataset, month_analysis

# dataset = InvestDataset()
# for i in dataset:
#     print(i)
#     dataset.download(i)

# test = month_analysis(1)
# for i in range(1,8):
#     test = month_analysis(i)
#     test.download()

# test.chart()
month_analysis(1) + month_analysis(2)
print(month_analysis(1) + month_analysis(2))
