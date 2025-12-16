#!/usr/bin/env python3
"""
Supabase Database Connection Test Script
This script helps you verify your Supabase connection string configuration.
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def test_connection():
    """Test database connection with detailed diagnostics"""
    
    print("=" * 60)
    print("🔍 SUPABASE CONNECTION TEST")
    print("=" * 60)
    
    # Step 1: Check if secrets file exists and is readable
    print("\n1️⃣ Checking secrets configuration...")
    try:
        if not hasattr(st, 'secrets'):
            print("   ❌ Streamlit secrets not accessible")
            return False
        
        if 'database' not in st.secrets:
            print("   ❌ 'database' section not found in secrets.toml")
            print("   💡 Add [database] section to .streamlit/secrets.toml")
            return False
        
        if 'url' not in st.secrets['database']:
            print("   ❌ 'url' key not found in [database] section")
            print("   💡 Add: url = \"your_connection_string\" under [database]")
            return False
        
        print("   ✅ Secrets configuration found")
        
    except Exception as e:
        print(f"   ❌ Error reading secrets: {str(e)}")
        return False
    
    # Step 2: Parse and validate connection string
    print("\n2️⃣ Validating connection string format...")
    try:
        url = st.secrets['database']['url']
        
        # Check if it starts with postgresql://
        if not url.startswith('postgresql://'):
            print("   ❌ Connection string should start with 'postgresql://'")
            return False
        
        # Parse connection string
        parts = url.replace('postgresql://', '').split('@')
        if len(parts) != 2:
            print("   ❌ Invalid connection string format")
            print("   💡 Format: postgresql://user:password@host:port/database")
            return False
        
        user_pass = parts[0]
        host_db = parts[1]
        
        # Check for password
        if ':' not in user_pass:
            print("   ❌ Password not found in connection string")
            print("   💡 Format: postgresql://postgres.xxx:PASSWORD@...")
            return False
        
        # Extract host and port
        host_port = host_db.split('/')[0].split('?')[0]
        if ':' in host_port:
            host, port = host_port.rsplit(':', 1)
            print(f"   ✅ Host: {host}")
            print(f"   ✅ Port: {port}")
        else:
            print("   ⚠️  Port not specified (will use default 5432)")
        
        # Check for SSL mode
        if 'sslmode' in url:
            print("   ✅ SSL mode configured")
        else:
            print("   ⚠️  SSL mode not specified (recommended: add ?sslmode=require)")
        
        print("   ✅ Connection string format looks valid")
        
    except Exception as e:
        print(f"   ❌ Error parsing connection string: {str(e)}")
        return False
    
    # Step 3: Test actual connection
    print("\n3️⃣ Testing database connection...")
    try:
        print("   🔄 Attempting to connect (timeout: 10 seconds)...")
        
        conn = psycopg2.connect(
            st.secrets['database']['url'],
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        
        print("   ✅ Connection established!")
        
        # Test query
        print("\n4️⃣ Testing database query...")
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"   ✅ PostgreSQL version: {version['version'][:50]}...")
        
        # Check if we can create tables
        print("\n5️⃣ Testing table creation permissions...")
        cur.execute("""
            SELECT has_schema_privilege('public', 'CREATE') as can_create;
        """)
        result = cur.fetchone()
        if result['can_create']:
            print("   ✅ Can create tables in public schema")
        else:
            print("   ⚠️  Cannot create tables - check permissions")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Database connection is working properly!")
        print("=" * 60)
        print("\n💡 Your Online Gyaan app should now connect successfully.")
        print("   Restart the app to apply the connection.\n")
        
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"   ❌ Connection failed: {error_msg}")
        
        print("\n🔧 TROUBLESHOOTING SUGGESTIONS:")
        
        if "timeout" in error_msg.lower():
            print("   • Connection timeout - check your internet connection")
            print("   • Verify the host address is correct")
            
        elif "password authentication failed" in error_msg.lower():
            print("   • Wrong password in connection string")
            print("   • Get password from Supabase: Settings → Database → Reset password")
            
        elif "server closed the connection" in error_msg.lower():
            print("   • Try adding ?sslmode=require to connection string")
            print("   • Try direct connection (port 5432) instead of pooler (6543)")
            print("   • Check IP allowlist in Supabase settings")
            
        elif "could not translate host name" in error_msg.lower():
            print("   • Invalid host address")
            print("   • Verify connection string from Supabase dashboard")
        
        else:
            print("   • Check Supabase project is active")
            print("   • Verify connection string is complete and correct")
            print("   • Check firewall/network settings")
        
        print("\n📋 CONNECTION STRING FORMAT:")
        print("   postgresql://postgres.PROJECT_REF:PASSWORD@HOST:PORT/postgres?sslmode=require")
        print("\n   Get it from: Supabase Dashboard → Settings → Database → Connection string")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
