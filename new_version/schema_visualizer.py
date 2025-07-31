import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import io
import base64

def create_schema_diagram():
    """Create a dynamic database schema diagram"""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    table_color = '#E8F4FD'
    border_color = '#2196F3'
    text_color = '#1976D2'
    
    # Define table structures
    tables = {
        'customers': {
            'position': (1, 7),
            'fields': [
                'id (SERIAL PRIMARY KEY)',
                'name (VARCHAR(100))',
                'email (VARCHAR(100))',
                'city (VARCHAR(50))',
                'created_at (TIMESTAMP)'
            ]
        },
        'products': {
            'position': (8, 7),
            'fields': [
                'id (SERIAL PRIMARY KEY)',
                'name (VARCHAR(100))',
                'price (DECIMAL(10,2))',
                'category (VARCHAR(50))',
                'stock_quantity (INTEGER)'
            ]
        },
        'orders': {
            'position': (4.5, 3),
            'fields': [
                'id (SERIAL PRIMARY KEY)',
                'customer_id (INTEGER)',
                'product_name (VARCHAR(100))',
                'amount (DECIMAL(10,2))',
                'order_date (TIMESTAMP)'
            ]
        }
    }
    
    # Draw tables
    for table_name, table_info in tables.items():
        x, y = table_info['position']
        fields = table_info['fields']
        
        # Calculate box dimensions
        width = 5
        height = 0.8 + len(fields) * 0.4
        
        # Draw table box
        box = FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle="round,pad=0.1",
            facecolor=table_color,
            edgecolor=border_color,
            linewidth=2
        )
        ax.add_patch(box)
        
        # Draw table title
        ax.text(x, y + height/2 - 0.2, table_name.upper(), 
                fontsize=12, fontweight='bold', ha='center', va='center',
                color=text_color)
        
        # Draw fields
        for i, field in enumerate(fields):
            ax.text(x - width/2 + 0.1, y + height/2 - 0.6 - i*0.4, field,
                    fontsize=9, ha='left', va='center', color='black')
    
    # Draw relationships
    # customers -> orders
    ax.annotate('', xy=(3.5, 4.5), xytext=(2.5, 6.8),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(3, 5.5, '1:N', fontsize=10, ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # products -> orders (through product_name)
    ax.annotate('', xy=(6.5, 4.5), xytext=(10.5, 6.8),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax.text(8.5, 5.5, '1:N', fontsize=10, ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # Add title
    ax.text(7, 9.5, 'Database Schema - Sample E-commerce System', 
            fontsize=16, fontweight='bold', ha='center', va='center',
            color=text_color)
    
    # Add description
    description = """
    This diagram shows the relationships between tables in the sample database.
    Users can ask questions like:
    • "Which customers have the most orders?"
    • "What are the top selling products?"
    • "Show me customers from New York"
    • "What's the total revenue by category?"
    """
    
    ax.text(7, 1, description, fontsize=10, ha='center', va='top',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='#F5F5F5', alpha=0.8))
    
    # Add legend
    legend_elements = [
        patches.Patch(color=table_color, label='Table'),
        patches.Patch(color='red', label='Customer-Order Relationship'),
        patches.Patch(color='green', label='Product-Order Relationship')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    plt.tight_layout()
    return fig

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string for Streamlit"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_str

def display_schema_diagram():
    """Display the schema diagram in Streamlit"""
    
    st.subheader("📊 Database Schema")
    
    # Create the diagram
    fig = create_schema_diagram()
    
    # Convert to base64 and display
    img_str = fig_to_base64(fig)
    
    # Display the image
    st.markdown(f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_str}" style="max-width: 100%; height: auto;">
    </div>
    """, unsafe_allow_html=True)
    
    # Add sample questions
    st.subheader("💡 Sample Questions You Can Ask")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Customer Analysis:**")
        st.markdown("""
        - "Which customers have the most orders?"
        - "Show me customers from New York"
        - "Find customers who spent more than $500"
        - "Which city has the most customers?"
        """)
        
        st.markdown("**Product Analysis:**")
        st.markdown("""
        - "What are the top selling products?"
        - "List all products with their prices"
        - "Show products in the Electronics category"
        - "What's the average price of products?"
        """)
    
    with col2:
        st.markdown("**Order Analysis:**")
        st.markdown("""
        - "Show orders from the last 30 days"
        - "What's the total revenue by category?"
        - "Find the highest value order"
        - "Show orders for customer John Doe"
        """)
        
        st.markdown("**Complex Queries:**")
        st.markdown("""
        - "Which customers bought Electronics products?"
        - "What's the total revenue per customer?"
        - "Show customers and their total spending"
        - "Find products with low stock (less than 10 items)"
        """)

def display_schema_text():
    """Display schema as text for fallback"""
    
    st.subheader("📊 Database Schema (Text Version)")
    
    schema_text = """
    **CUSTOMERS Table:**
    - id (SERIAL PRIMARY KEY)
    - name (VARCHAR(100))
    - email (VARCHAR(100))
    - city (VARCHAR(50))
    - created_at (TIMESTAMP)

    **PRODUCTS Table:**
    - id (SERIAL PRIMARY KEY)
    - name (VARCHAR(100))
    - price (DECIMAL(10,2))
    - category (VARCHAR(50))
    - stock_quantity (INTEGER)

    **ORDERS Table:**
    - id (SERIAL PRIMARY KEY)
    - customer_id (INTEGER) → References customers.id
    - product_name (VARCHAR(100)) → Links to products.name
    - amount (DECIMAL(10,2))
    - order_date (TIMESTAMP)

    **Relationships:**
    - CUSTOMERS ──(1:N)──> ORDERS (via customer_id)
    - PRODUCTS ──(1:N)──> ORDERS (via product_name)
    """
    
    st.code(schema_text, language='sql')

def show_schema_visualizer():
    """Main function to show schema visualizer"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Schema Information")
    
    # Try to show diagram, fallback to text if matplotlib fails
    try:
        display_schema_diagram()
    except Exception as e:
        st.warning("Could not generate diagram. Showing text version.")
        display_schema_text()
    
    # Add download button for schema info
    schema_info = """
    # Database Schema - Sample E-commerce System

    ## Tables:
    - CUSTOMERS: id, name, email, city, created_at
    - PRODUCTS: id, name, price, category, stock_quantity  
    - ORDERS: id, customer_id, product_name, amount, order_date

    ## Relationships:
    - CUSTOMERS ──(1:N)──> ORDERS (via customer_id)
    - PRODUCTS ──(1:N)──> ORDERS (via product_name)

    ## Sample Questions:
    - "Which customers have the most orders?"
    - "What are the top selling products?"
    - "Show me customers from New York"
    - "What's the total revenue by category?"
    """
    
    st.download_button(
        label="📥 Download Schema Info",
        data=schema_info,
        file_name="database_schema.md",
        mime="text/markdown"
    ) 