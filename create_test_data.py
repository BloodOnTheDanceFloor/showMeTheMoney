import pandas as pd
import numpy as np
import os

def create_test_excel():
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    
    # Generate realistic stock data
    np.random.seed(42)
    base_price = 100
    
    data = []
    for i, date in enumerate(dates):
        # Random price movement
        change = np.random.normal(0, 2)
        open_price = base_price + change
        
        # Ensure high >= low and high >= open/close, low <= open/close
        high = max(open_price, base_price) + np.random.uniform(0, 2)
        low = min(open_price, base_price) - np.random.uniform(0, 2)
        close = base_price + np.random.normal(0, 1.5)
        
        # Ensure price relationships
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Generate turnover (in millions)
        turnover = np.random.uniform(50, 200) * 1e6
        
        data.append({
            '时间': date.strftime('%Y-%m-%d'),
            '开盘': round(open_price, 2),
            '最高': round(high, 2),
            '最低': round(low, 2),
            '收盘': round(close, 2),
            '成交额': round(turnover, 0)
        })
        
        base_price = close
    
    df = pd.DataFrame(data)
    
    # Save to Excel file
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data.xlsx")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Write title in A1
        pd.DataFrame([['测试股票数据']]).to_excel(writer, index=False, header=False, startrow=0, startcol=0)
        
        # Write data starting from row 3 (row 2 will be empty)
        df.to_excel(writer, index=False, startrow=2, startcol=0)
    
    print(f"Test Excel file created at: {excel_path}")
    print("Sample data:")
    print(df.head())

if __name__ == "__main__":
    create_test_excel()