
from odoo import api, models
import pandas as pd
import numpy as np
from datetime import timedelta

class PredictiveEngine(models.Model):
    _name = 'predictive.engine'
    
    # Main data preparation method
    def prepare_training_data(self, lookback_days=365):
        """Orchestrates the full feature engineering pipeline"""
        raw_df = self._extract_raw_data()
        df = self._clean_data(raw_df)
        df = self._add_time_features(df)
        df = self._add_rolling_features(df, lookback_days)
        df = self._add_inventory_features(df)
        return df

    # Step 1: Data Extraction
    def _extract_raw_data(self):
        """Pull raw data from Odoo tables"""
        sales = self.env['sale.order'].search_read(
            [('state', '=', 'sale')],
            ['date_order', 'product_id', 'product_uom_qty', 'price_unit']
        )
        inventory = self.env['stock.move'].search_read(
            [],
            ['product_id', 'date', 'quantity_done']
        )
        return {
            'sales': pd.DataFrame(sales),
            'inventory': pd.DataFrame(inventory)
        }

    # Step 2: Data Cleaning
    def _clean_data(self, raw_data):
        """Handle missing values and type conversions"""
        df = raw_data['sales'].copy()
        
        # Convert and filter dates
        df['date'] = pd.to_datetime(df['date_order']).dt.date
        df = df[df['date'] > (pd.to_datetime('today') - pd.DateOffset(years=1)).date()]
        
        # Drop nulls
        df.dropna(subset=['product_id', 'product_uom_qty'], inplace=True)
        return df

    # Step 3: Time Features
    def _add_time_features(self, df):
        """Add temporal indicators"""
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['is_month_end'] = pd.to_datetime(df['date']).dt.is_month_end.astype(int)
        return df

    # Step 4: Rolling Features
    def _add_rolling_features(self, df, window_days):
        """Calculate moving averages and trends"""
        df = df.sort_values(['product_id', 'date'])
        
        # Group by product to calculate product-specific features
        grouped = df.groupby('product_id')
        
        # Rolling averages
        df['7d_avg_sales'] = grouped['product_uom_qty'].transform(
            lambda x: x.rolling(window='7D', on=df['date']).mean()
        )
        
        # Growth rate
        df['sales_growth_30d'] = grouped['product_uom_qty'].transform(
            lambda x: x.rolling(window='30D', on=df['date']).mean() / 
                      x.rolling(window='60D', on=df['date']).mean() - 1
        )
        return df

    # Step 5: Inventory Features
    def _add_inventory_features(self, df):
        """Merge and calculate inventory ratios"""
        inventory = self.env['stock.quant'].search_read(
            [],
            ['product_id', 'quantity', 'date']
        )
        inventory_df = pd.DataFrame(inventory)
        
        if not inventory_df.empty:
            inventory_df['date'] = pd.to_datetime(inventory_df['date']).dt.date
            df = pd.merge_asof(
                df.sort_values('date'),
                inventory_df.sort_values('date'),
                on='date',
                by='product_id',
                direction='backward'
            )
            df['demand_supply_ratio'] = df['product_uom_qty'] / (df['quantity'] + 1e-6)
        return df


    def generate_and_act_on_predictions(self):
        """Main method to run predictions and trigger automations"""
        try:
            # 1. Prepare data and train model (using your existing methods)
            df = self.prepare_training_data()
            model = self._train_model(df)
            
            # 2. Generate predictions for next 30 days
            predictions = self._generate_predictions(model, df)
            
            # 3. Trigger automated actions
            self._trigger_inventory_alerts(predictions)
            self._flag_sales_opportunities(predictions)
            
            return "Predictions and automations completed successfully"
        except Exception as e:
            return f"Error: {str(e)}"

    def _train_model(self, df):
        """Example model training (simplified)"""
        from sklearn.ensemble import RandomForestRegressor
        X = df[['day_of_week', 'month', '7d_avg_sales', 'demand_supply_ratio']]
        y = df['product_uom_qty']
        return RandomForestRegressor(n_estimators=50).fit(X, y)

    def _generate_predictions(self, model, df):
        """Generate predictions for all products"""
        products = self.env['product.product'].search([])
        predictions = {}
        
        for product in products:
            # Get latest product data
            latest = df[df['product_id'] == product.id].iloc[-1]
            
            # Create input features
            input_data = [[
                pd.Timestamp.today().dayofweek,  # Current day of week
                pd.Timestamp.today().month,      # Current month
                latest['7d_avg_sales'],
                latest['demand_supply_ratio']
            ]]
            
            predictions[product.id] = model.predict(input_data)[0]
        
        return predictions

    def _trigger_inventory_alerts(self, predictions):
        """Create procurement alerts for low stock"""
        Alert = self.env['stock.warehouse.orderpoint']
        
        for product in self.env['product.product'].search([]):
            predicted_demand = predictions.get(product.id, 0)
            current_stock = product.qty_available
            
            if current_stock < predicted_demand:
                # Create or update reorder rule
                Alert.create({
                    'product_id': product.id,
                    'product_min_qty': predicted_demand * 1.2,  # 20% buffer
                    'product_max_qty': predicted_demand * 1.5,
                    'warehouse_id': self.env['stock.warehouse'].search([], limit=1).id
                })
                
                # Post chatter message
                product.message_post(
                    body=f"Auto-generated reorder rule: Predicted demand {predicted_demand:.0f} units"
                )

    def _flag_sales_opportunities(self, predictions):
        """Tag high-growth potential products"""
        tag = self.env.ref('sales_team.tag_sales_opportunity', raise_if_not_found=False)
        if not tag:
            tag = self.env['res.partner.category'].create({
                'name': 'Sales Opportunity'
            })
        
        for product in self.env['product.product'].search([]):
            if predictions.get(product.id, 0) > product.qty_available * 1.5:
                product.write({
                    'category_id': [(4, tag.id)]  # Add tag without removing existing
                })