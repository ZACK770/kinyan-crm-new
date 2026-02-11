"""
סקריפט לניתוח שגיאות חוזרות ונשנות באפליקציה
מנתח audit logs ומזהה דפוסים של שגיאות, בעיות נפוצות, ופעולות כושלות
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_db_session
from db.models import AuditLog, User


class ErrorAnalyzer:
    """מנתח שגיאות ובעיות חוזרות במערכת"""
    
    def __init__(self, days: int = 7):
        self.days = days
        self.since = datetime.utcnow() - timedelta(days=days)
        
    async def analyze(self):
        """הרצת ניתוח מלא"""
        print("=" * 80)
        print(f"🔍 ניתוח שגיאות חוזרות - {self.days} ימים אחרונים")
        print("=" * 80)
        print()
        
        async for db in get_db_session():
            try:
                # 1. ניתוח פעולות כושלות
                await self._analyze_failed_actions(db)
                
                # 2. ניתוח שגיאות לפי סוג ישות
                await self._analyze_errors_by_entity(db)
                
                # 3. ניתוח שגיאות לפי משתמש
                await self._analyze_errors_by_user(db)
                
                # 4. ניתוח דפוסים חשודים
                await self._analyze_suspicious_patterns(db)
                
                # 5. סטטיסטיקות כלליות
                await self._general_statistics(db)
                
                # 6. המלצות לתיקון
                await self._recommendations(db)
                
            finally:
                await db.close()
    
    async def _analyze_failed_actions(self, db: AsyncSession):
        """ניתוח פעולות שנכשלו או הסתיימו בשגיאה"""
        print("📊 פעולות כושלות")
        print("-" * 80)
        
        # חיפוש לוגים עם אינדיקציות לשגיאות
        error_keywords = ['error', 'failed', 'exception', 'שגיאה', 'נכשל', 'כשל']
        
        query = (
            select(AuditLog)
            .where(AuditLog.created_at >= self.since)
            .order_by(desc(AuditLog.created_at))
        )
        
        result = await db.execute(query)
        all_logs = result.scalars().all()
        
        # סינון לוגים עם שגיאות
        error_logs = []
        for log in all_logs:
            desc_lower = (log.description or "").lower()
            if any(keyword in desc_lower for keyword in error_keywords):
                error_logs.append(log)
        
        if not error_logs:
            print("✅ לא נמצאו שגיאות מתועדות")
            print()
            return
        
        print(f"⚠️  נמצאו {len(error_logs)} שגיאות מתועדות\n")
        
        # קיבוץ לפי סוג פעולה
        action_errors = Counter(log.action for log in error_logs)
        print("שגיאות לפי סוג פעולה:")
        for action, count in action_errors.most_common(10):
            print(f"  • {action}: {count} פעמים")
        
        print()
        
        # הצגת 5 השגיאות האחרונות
        print("5 השגיאות האחרונות:")
        for i, log in enumerate(error_logs[:5], 1):
            print(f"\n  {i}. {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     פעולה: {log.action}")
            print(f"     משתמש: {log.user_name or 'מערכת'}")
            print(f"     תיאור: {log.description[:100]}...")
            if log.entity_type:
                print(f"     ישות: {log.entity_type} (ID: {log.entity_id})")
        
        print()
    
    async def _analyze_errors_by_entity(self, db: AsyncSession):
        """ניתוח שגיאות לפי סוג ישות"""
        print("📋 שגיאות לפי סוג ישות")
        print("-" * 80)
        
        query = (
            select(
                AuditLog.entity_type,
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            )
            .where(AuditLog.created_at >= self.since)
            .where(AuditLog.entity_type.isnot(None))
            .group_by(AuditLog.entity_type, AuditLog.action)
            .order_by(desc('count'))
        )
        
        result = await db.execute(query)
        entity_stats = result.all()
        
        if not entity_stats:
            print("אין נתונים")
            print()
            return
        
        # קיבוץ לפי ישות
        by_entity = defaultdict(list)
        for entity_type, action, count in entity_stats:
            by_entity[entity_type].append((action, count))
        
        for entity_type, actions in sorted(by_entity.items(), key=lambda x: sum(a[1] for a in x[1]), reverse=True)[:10]:
            total = sum(count for _, count in actions)
            print(f"\n{entity_type}: {total} פעולות")
            for action, count in sorted(actions, key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {action}: {count}")
        
        print()
    
    async def _analyze_errors_by_user(self, db: AsyncSession):
        """ניתוח פעילות לפי משתמש"""
        print("👥 פעילות לפי משתמש")
        print("-" * 80)
        
        query = (
            select(
                AuditLog.user_name,
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            )
            .where(AuditLog.created_at >= self.since)
            .where(AuditLog.user_name.isnot(None))
            .group_by(AuditLog.user_name, AuditLog.action)
            .order_by(desc('count'))
        )
        
        result = await db.execute(query)
        user_stats = result.all()
        
        if not user_stats:
            print("אין נתונים")
            print()
            return
        
        # קיבוץ לפי משתמש
        by_user = defaultdict(list)
        for user_name, action, count in user_stats:
            by_user[user_name].append((action, count))
        
        print("משתמשים פעילים:")
        for user_name, actions in sorted(by_user.items(), key=lambda x: sum(a[1] for a in x[1]), reverse=True)[:10]:
            total = sum(count for _, count in actions)
            print(f"\n{user_name}: {total} פעולות")
            for action, count in sorted(actions, key=lambda x: x[1], reverse=True)[:3]:
                print(f"  • {action}: {count}")
        
        print()
    
    async def _analyze_suspicious_patterns(self, db: AsyncSession):
        """זיהוי דפוסים חשודים"""
        print("🔎 דפוסים חשודים")
        print("-" * 80)
        
        # 1. פעולות delete מרובות
        delete_query = (
            select(func.count(AuditLog.id))
            .where(AuditLog.created_at >= self.since)
            .where(AuditLog.action == 'delete')
        )
        delete_result = await db.execute(delete_query)
        delete_count = delete_result.scalar_one()
        
        if delete_count > 50:
            print(f"⚠️  מספר גבוה של מחיקות: {delete_count}")
        
        # 2. פעולות מאותו IP בזמן קצר
        ip_query = (
            select(
                AuditLog.ip_address,
                func.count(AuditLog.id).label('count')
            )
            .where(AuditLog.created_at >= self.since)
            .where(AuditLog.ip_address.isnot(None))
            .group_by(AuditLog.ip_address)
            .order_by(desc('count'))
            .limit(5)
        )
        
        ip_result = await db.execute(ip_query)
        ip_stats = ip_result.all()
        
        if ip_stats:
            print("\nכתובות IP פעילות ביותר:")
            for ip, count in ip_stats:
                if count > 1000:
                    print(f"  ⚠️  {ip}: {count} פעולות (חשוד)")
                else:
                    print(f"  • {ip}: {count} פעולות")
        
        # 3. כשלונות התחברות
        login_fail_query = (
            select(func.count(AuditLog.id))
            .where(AuditLog.created_at >= self.since)
            .where(AuditLog.action == 'login')
            .where(or_(
                AuditLog.description.like('%failed%'),
                AuditLog.description.like('%נכשל%')
            ))
        )
        
        login_fail_result = await db.execute(login_fail_query)
        login_fails = login_fail_result.scalar_one()
        
        if login_fails > 0:
            print(f"\n⚠️  ניסיונות התחברות כושלים: {login_fails}")
        
        if delete_count <= 50 and login_fails == 0:
            print("✅ לא נמצאו דפוסים חשודים")
        
        print()
    
    async def _general_statistics(self, db: AsyncSession):
        """סטטיסטיקות כלליות"""
        print("📈 סטטיסטיקות כלליות")
        print("-" * 80)
        
        # סה"כ פעולות
        total_query = select(func.count(AuditLog.id)).where(AuditLog.created_at >= self.since)
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()
        
        # פעולות לפי יום
        daily_avg = total / self.days if self.days > 0 else 0
        
        # סוגי פעולות
        action_query = (
            select(AuditLog.action, func.count(AuditLog.id).label('count'))
            .where(AuditLog.created_at >= self.since)
            .group_by(AuditLog.action)
            .order_by(desc('count'))
        )
        action_result = await db.execute(action_query)
        actions = action_result.all()
        
        print(f"סה\"כ פעולות: {total}")
        print(f"ממוצע יומי: {daily_avg:.1f}")
        print(f"\nפילוח לפי סוג פעולה:")
        for action, count in actions[:10]:
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  • {action}: {count} ({percentage:.1f}%)")
        
        print()
    
    async def _recommendations(self, db: AsyncSession):
        """המלצות לתיקון ושיפור"""
        print("💡 המלצות")
        print("-" * 80)
        
        recommendations = []
        
        # בדיקת שגיאות חוזרות
        error_keywords = ['error', 'failed', 'exception', 'שגיאה', 'נכשל']
        query = select(AuditLog).where(AuditLog.created_at >= self.since)
        result = await db.execute(query)
        all_logs = result.scalars().all()
        
        error_count = sum(1 for log in all_logs 
                         if any(kw in (log.description or "").lower() for kw in error_keywords))
        
        if error_count > 10:
            recommendations.append(
                f"נמצאו {error_count} שגיאות מתועדות - מומלץ לבדוק לוגים מפורטים"
            )
        
        # בדיקת פעילות נמוכה
        if len(all_logs) < 100:
            recommendations.append(
                "פעילות נמוכה במערכת - ייתכן שיש בעיה בלוגינג או שהמערכת לא בשימוש"
            )
        
        # בדיקת משתמשים
        user_query = select(func.count(func.distinct(AuditLog.user_id))).where(
            and_(
                AuditLog.created_at >= self.since,
                AuditLog.user_id.isnot(None)
            )
        )
        user_result = await db.execute(user_query)
        unique_users = user_result.scalar_one()
        
        if unique_users < 2:
            recommendations.append(
                "מספר משתמשים פעילים נמוך - ייתכן שיש בעיה באימות או בהרשאות"
            )
        
        if not recommendations:
            recommendations.append("✅ המערכת נראית תקינה - לא נמצאו בעיות משמעותיות")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        print()
        print("=" * 80)


async def main():
    """נקודת כניסה ראשית"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ניתוח שגיאות חוזרות במערכת CRM')
    parser.add_argument('--days', type=int, default=7, help='מספר ימים לניתוח (ברירת מחדל: 7)')
    
    args = parser.parse_args()
    
    analyzer = ErrorAnalyzer(days=args.days)
    await analyzer.analyze()


if __name__ == "__main__":
    asyncio.run(main())
