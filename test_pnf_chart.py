import os
import sys

# Add the parent directory to the path so we can import from apps
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.pnf.pnf_chart import PNFChart

def test_pnf_chart():
    # Test with a sample Excel file
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"Test file not found: {excel_path}")
        print("Please create a test Excel file with columns: 时间, 最高, 最低, 开盘, 收盘, 成交额")
        return
    
    # Create PNF chart instance
    pnf_chart = PNFChart(excel_path, reversal_boxes=1, box_size_value=1.0)
    
    # Load data
    if pnf_chart.load_data():
        print("Data loaded successfully!")
        print(f"Data shape: {pnf_chart.data.shape}")
        print(f"Columns: {pnf_chart.data.columns.tolist()}")
        print(f"First few rows:")
        print(pnf_chart.data.head())
        
        # Calculate PNF
        if pnf_chart.calculate_pnf():
            print("PNF calculation successful!")
            print(f"Chart data length: {len(pnf_chart.chart_data)}")
            print(f"Mark points count: {len(pnf_chart.mark_points)}")
            
            # Check if turnover is in mark_points
            if pnf_chart.mark_points:
                first_mark = pnf_chart.mark_points[0]
                print(f"First mark keys: {first_mark.keys()}")
                if 'turnover' in first_mark:
                    print(f"First mark turnover: {first_mark['turnover']}")
                else:
                    print("Turnover not found in mark_points!")
            
            # Check column turnovers
            column_turnovers = {}
            for mp in pnf_chart.mark_points:
                col = mp['col']
                turnover = mp.get('turnover', 0)
                if col not in column_turnovers:
                    column_turnovers[col] = 0
                column_turnovers[col] += turnover
            
            print(f"Column turnovers (first 5 columns):")
            for col in sorted(column_turnovers.keys())[:5]:
                print(f"  Column {col}: {column_turnovers[col]:,.2f}")
        else:
            print("PNF calculation failed!")
    else:
        print("Data loading failed!")

if __name__ == "__main__":
    test_pnf_chart()