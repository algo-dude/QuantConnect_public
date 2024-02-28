# region imports
from AlgorithmImports import *
from QuantConnect.Data import Slice
# endregion

# Fee model to test zero fees
class CustomFeeModel(FeeModel):
    def __init__(self):
        pass  
    def GetOrderFee(self, parameters: OrderFeeParameters) -> OrderFee:
        return OrderFee.Zero

# Buying power model so that we can aoivd trading single shares
class MinimumOrderSizeBuyingPowerModel(BuyingPowerModel):
    def __init__(self, min_order_size):
        self.min_order_size = min_order_size

    def GetMinimumOrderQuantityForResolution(self, security, targetOrderValue):
        return OrderQuantity(self.min_order_size, 0)

    def GetBuyingPower(self, parameters):
        return BuyingPower(self.Portfolio.Cash, 0)



class Vwaptrend(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2018, 11, 10)
        self.SetEndDate(2023, 11, 11)
        self.SetCash(25000)
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel()) # Equal weighting with assets
        self.SetExecution(ImmediateExecutionModel())
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        self.asset1 = self.AddEquity("QQQ", Resolution.Minute)
        self.asset1.SetDataNormalizationMode(DataNormalizationMode.Raw)
        self.asset1.SetBuyingPowerModel(MinimumOrderSizeBuyingPowerModel(10))  # Set minimum order size to 10 so that insights don't trade single shares

        self.asset1_vwap = self.VWAP(self.asset1.Symbol)
        self.asset1_long = None

        self.period = timedelta(days=1) # Insight period, but we're not using it here as the execution model is with market orders

        # Turn off fees here, comment out for normal IB fees
        # self.asset1.SetFeeModel(CustomFeeModel())

    def OnData(self, slice: Slice) -> None:
        if not self.asset1_vwap.IsReady or (self.Time.hour == 9 and self.Time.minute == 30) or (self.Time.hour == 16 and self.Time.minute == 0):
            return

        # exit position EOD
        if self.Time.hour == 15 and self.Time.minute == 59:
            asset1_insight = Insight.Price(self.asset1.Symbol, self.period, InsightDirection.Flat)
            self.EmitInsights(asset1_insight)
            self.Log(f'Exiting position at EOD')
            self.asset1_long = None
            return
        
        # If getting second resolution data but don't want to trade every second
        # if not self.Time.second == 0:
        #     return
        
        # If we want to trade every 5 minutes
        # if not self.Time.minute % 5 == 0:
        #     return
        
        price1 = self.asset1.Close
        vwap1 = round(self.asset1_vwap.Current.Value, 2)
        diff = price1 - vwap1
        minimum = 0
        if diff > minimum and (not self.asset1_long or self.asset1_long is None):
            asset1_insight = Insight.Price(self.asset1.Symbol, self.period, InsightDirection.Up)
            self.EmitInsights(asset1_insight)
            self.asset1_long = True
            self.Log(f'vwap: {round(self.asset1_vwap.Current.Value, 2)} price: {price1} Flipping to long')

        if diff < -1 * minimum and (self.asset1_long or self.asset1_long is None):
            asset1_insight = Insight.Price(self.asset1.Symbol, self.period, InsightDirection.Down)
            self.EmitInsights(asset1_insight)
            self.asset1_long = False
            self.Log(f'vwap: {round(self.asset1_vwap.Current.Value, 2)} price: {price1} Flipping to short')

        # do this every few minutes
        # if self.Time.minute % 1  == 0:    
        #     self.Plot("IntradayVwap", "vwap", self.asset1_vwap.Current.Value)
        #     self.Plot("IntradayVwap", "price", price1)
        #     self.Log(f"vwap: {self.asset1_vwap.Current.Value} price: {price1}")




