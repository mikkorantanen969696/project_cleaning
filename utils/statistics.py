import pandas as pd
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from database.models import Order, User, City, Payment, OrderStatus, UserRole
from database.database import get_session
import openpyxl
from io import BytesIO

class StatisticsManager:
    def __init__(self):
        pass
    
    async def get_general_stats(self, start_date=None, end_date=None):
        async with get_session() as session:
            query = select(Order)
            
            if start_date:
                query = query.where(Order.created_at >= start_date)
            if end_date:
                query = query.where(Order.created_at <= end_date)
            
            result = await session.execute(query)
            orders = result.scalars().all()
            
            total_orders = len(orders)
            completed_orders = len([o for o in orders if o.status == OrderStatus.COMPLETED])
            cancelled_orders = len([o for o in orders if o.status == OrderStatus.CANCELLED])
            
            total_revenue = sum(o.price for o in orders if o.status == OrderStatus.COMPLETED)
            avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
            
            return {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'cancelled_orders': cancelled_orders,
                'completion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0,
                'total_revenue': total_revenue,
                'avg_order_value': avg_order_value
            }
    
    async def get_manager_stats(self, manager_id=None, start_date=None, end_date=None):
        async with get_session() as session:
            query = select(Order)
            
            if manager_id:
                query = query.where(Order.manager_id == manager_id)
            
            if start_date:
                query = query.where(Order.created_at >= start_date)
            if end_date:
                query = query.where(Order.created_at <= end_date)
            
            result = await session.execute(query)
            orders = result.scalars().all()
            
            # Group by manager
            manager_stats = {}
            for order in orders:
                manager_id = order.manager_id
                if manager_id not in manager_stats:
                    manager_stats[manager_id] = {
                        'orders': [],
                        'total_revenue': 0,
                        'completed_orders': 0
                    }
                
                manager_stats[manager_id]['orders'].append(order)
                if order.status == OrderStatus.COMPLETED:
                    manager_stats[manager_id]['total_revenue'] += order.price
                    manager_stats[manager_id]['completed_orders'] += 1
            
            # Get manager names
            manager_names = {}
            for manager_id in manager_stats.keys():
                manager = await session.get(User, manager_id)
                manager_names[manager_id] = manager.full_name if manager else "Unknown"
            
            # Format results
            result = []
            for manager_id, stats in manager_stats.items():
                result.append({
                    'manager_id': manager_id,
                    'manager_name': manager_names[manager_id],
                    'total_orders': len(stats['orders']),
                    'completed_orders': stats['completed_orders'],
                    'total_revenue': stats['total_revenue'],
                    'completion_rate': (stats['completed_orders'] / len(stats['orders']) * 100) if stats['orders'] else 0
                })
            
            return result
    
    async def get_cleaner_stats(self, cleaner_id=None, start_date=None, end_date=None):
        async with get_session() as session:
            query = select(Order).where(Order.cleaner_id.isnot(None))
            
            if cleaner_id:
                query = query.where(Order.cleaner_id == cleaner_id)
            
            if start_date:
                query = query.where(Order.created_at >= start_date)
            if end_date:
                query = query.where(Order.created_at <= end_date)
            
            result = await session.execute(query)
            orders = result.scalars().all()
            
            # Group by cleaner
            cleaner_stats = {}
            for order in orders:
                cleaner_id = order.cleaner_id
                if cleaner_id not in cleaner_stats:
                    cleaner_stats[cleaner_id] = {
                        'orders': [],
                        'total_revenue': 0,
                        'completed_orders': 0
                    }
                
                cleaner_stats[cleaner_id]['orders'].append(order)
                if order.status == OrderStatus.COMPLETED:
                    cleaner_stats[cleaner_id]['total_revenue'] += order.price
                    cleaner_stats[cleaner_id]['completed_orders'] += 1
            
            # Get cleaner names
            cleaner_names = {}
            for cleaner_id in cleaner_stats.keys():
                cleaner = await session.get(User, cleaner_id)
                cleaner_names[cleaner_id] = cleaner.full_name if cleaner else "Unknown"
            
            # Format results
            result = []
            for cleaner_id, stats in cleaner_stats.items():
                result.append({
                    'cleaner_id': cleaner_id,
                    'cleaner_name': cleaner_names[cleaner_id],
                    'total_orders': len(stats['orders']),
                    'completed_orders': stats['completed_orders'],
                    'total_revenue': stats['total_revenue'],
                    'completion_rate': (stats['completed_orders'] / len(stats['orders']) * 100) if stats['orders'] else 0
                })
            
            return result
    
    async def get_city_stats(self, city_id=None, start_date=None, end_date=None):
        async with get_session() as session:
            query = select(Order)
            
            if city_id:
                query = query.where(Order.city_id == city_id)
            
            if start_date:
                query = query.where(Order.created_at >= start_date)
            if end_date:
                query = query.where(Order.created_at <= end_date)
            
            result = await session.execute(query)
            orders = result.scalars().all()
            
            # Group by city
            city_stats = {}
            for order in orders:
                city_id = order.city_id
                if city_id not in city_stats:
                    city_stats[city_id] = {
                        'orders': [],
                        'total_revenue': 0,
                        'completed_orders': 0
                    }
                
                city_stats[city_id]['orders'].append(order)
                if order.status == OrderStatus.COMPLETED:
                    city_stats[city_id]['total_revenue'] += order.price
                    city_stats[city_id]['completed_orders'] += 1
            
            # Get city names
            city_names = {}
            for city_id in city_stats.keys():
                city = await session.get(City, city_id)
                city_names[city_id] = city.name if city else "Unknown"
            
            # Format results
            result = []
            for city_id, stats in city_stats.items():
                result.append({
                    'city_id': city_id,
                    'city_name': city_names[city_id],
                    'total_orders': len(stats['orders']),
                    'completed_orders': stats['completed_orders'],
                    'total_revenue': stats['total_revenue'],
                    'completion_rate': (stats['completed_orders'] / len(stats['orders']) * 100) if stats['orders'] else 0
                })
            
            return result
    
    async def export_to_excel(self, stats_data, filename="statistics"):
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # General stats
            if 'general' in stats_data:
                df_general = pd.DataFrame([stats_data['general']])
                df_general.to_excel(writer, sheet_name='Общая статистика', index=False)
            
            # Manager stats
            if 'managers' in stats_data:
                df_managers = pd.DataFrame(stats_data['managers'])
                df_managers.to_excel(writer, sheet_name='Менеджеры', index=False)
            
            # Cleaner stats
            if 'cleaners' in stats_data:
                df_cleaners = pd.DataFrame(stats_data['cleaners'])
                df_cleaners.to_excel(writer, sheet_name='Клинеры', index=False)
            
            # City stats
            if 'cities' in stats_data:
                df_cities = pd.DataFrame(stats_data['cities'])
                df_cities.to_excel(writer, sheet_name='Города', index=False)
        
        output.seek(0)
        return output
    
    async def get_period_stats(self, start_date, end_date):
        """Get statistics for a specific period"""
        general_stats = await self.get_general_stats(start_date, end_date)
        manager_stats = await self.get_manager_stats(start_date=start_date, end_date=end_date)
        cleaner_stats = await self.get_cleaner_stats(start_date=start_date, end_date=end_date)
        city_stats = await self.get_city_stats(start_date=start_date, end_date=end_date)
        
        return {
            'period': {
                'start_date': start_date.strftime('%d.%m.%Y'),
                'end_date': end_date.strftime('%d.%m.%Y')
            },
            'general': general_stats,
            'managers': manager_stats,
            'cleaners': cleaner_stats,
            'cities': city_stats
        }
