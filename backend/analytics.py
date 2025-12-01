#imports
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from sqlalchemy import text

#set Plotly to render charts using the browser
# pio.renderers.default = "browser"  # Commented out for server environments (Flask/Gunicorn)

def get_portfolio_timeline_data(user_id=None):
    """Fetch portfolio total value over time from database, filtered by user if provided"""
    from .models import db, Position

    # Query to get Account Total for each date
    # Also exclude "Unknown" dates
    if user_id:
        positions = db.session.query(Position.Date, Position.Mkt_Val).filter(
            Position.Symbol == 'Account Total',
            Position.user_id == user_id,
            Position.Mkt_Val.isnot(None),
            Position.Date != 'Unknown',
            Position.Date.isnot(None)
        ).order_by(Position.Date).all()
    else:
        positions = db.session.query(Position.Date, Position.Mkt_Val).filter(
            Position.Symbol == 'Account Total',
            Position.Mkt_Val.isnot(None),
            Position.Date != 'Unknown',
            Position.Date.isnot(None)
        ).order_by(Position.Date).all()

    # Convert to dataframe
    if positions:
        data = []
        for pos in positions:
            try:
                # Clean the Mkt_Val string (remove $ and commas, convert to float)
                cleaned_value = float(str(pos.Mkt_Val).replace('$', '').replace(',', ''))
                data.append({'Date': pos.Date, 'portfolio_value': cleaned_value})
            except (ValueError, TypeError):
                continue
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(columns=['Date', 'portfolio_value'])

    # Return empty dataframe if no data
    if df.empty:
        return df

    # Convert portfolio_value to numeric
    df['portfolio_value'] = pd.to_numeric(df['portfolio_value'], errors='coerce')

    # Convert Date to datetime, handling invalid dates
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Remove rows with invalid dates
    df = df.dropna(subset=['Date'])

    # Sort by date to ensure chronological order
    df = df.sort_values('Date').reset_index(drop=True)

    return df

def get_FAKE_portfolio_timeline_data():
    """Fetch portfolio total value over time from database"""
    from .models import db, Position

    # Query to get account total for each date
    positions = db.session.query(Position.Date, Position.Mkt_Val).filter(
        Position.Symbol == 'Account Total'
    ).order_by(Position.Date).all()

    # Convert to dataframe
    if positions:
        data = []
        for pos in positions:
            try:
                cleaned_value = float(str(pos.Mkt_Val).replace('$', '').replace(',', ''))
                data.append({'Date': pos.Date, 'portfolio_value': cleaned_value})
            except (ValueError, TypeError):
                continue
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(columns=['Date', 'portfolio_value'])

    # Convert portfolio_value to numeric
    df['portfolio_value'] = pd.to_numeric(df['portfolio_value'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Sort by date to ensure chronological order
    df = df.sort_values('Date').reset_index(drop=True)

    return df

def create_animated_timeline_graph(user_id=None):
    """Create an animated line graph showing portfolio growth over time with smooth CSS animation"""
    df = get_portfolio_timeline_data(user_id)

    # Create the complete figure with all data
    fig = go.Figure()

    # Add the main line trace with all data
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['portfolio_value'],
        mode='lines+markers',
        line=dict(color='#293949', width=3, shape='spline', smoothing=1.3),
        marker=dict(size=8, color='#293949'),
        fill='tozeroy',
        fillcolor='rgba(41, 57, 73, 0.1)',
        name='Portfolio Value'
    ))

    # Update layout with fixed axis ranges
    fig.update_layout(
        title={
            'text': 'Your Portfolio Value Over Time',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#F9F9F9', family='ClashDisplay'),
        },
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9'),
            tickformat='%m/%d/%Y',
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[df['Date'].min(), df['Date'].max()],
            showspikes=True,
            spikemode='across',
            spikesnap='data',
            spikecolor='rgba(249, 249, 249, 0.4)',
            spikethickness=1,
            spikedash='dot'
        ),
        yaxis=dict(
            title=dict(text='Portfolio Value ($)', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9', family='ClashDisplay'),
            tickformat='$,.0f',
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[0, df['portfolio_value'].max() * 1.1]
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#F9F9F9', family='ClashDisplay'),
        hovermode='x unified'
    )

    # Convert to HTML with custom JavaScript for smooth animation
    html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='animated-timeline',
        config={'displayModeBar': False}
    )

    # Add custom JavaScript for smooth SVG path animation
    animation_script = """
    <style>
        #animated-timeline .scatterlayer path.js-line {
            stroke-dasharray: 3000;
            stroke-dashoffset: 3000;
            animation: dash 6s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer path.js-fill {
            opacity: 0;
            animation: fillFade 3s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer .point {
            opacity: 0;
            animation: pointFade 3s ease-in-out forwards;
        }

        @keyframes dash {
            to {
                stroke-dashoffset: 0;
            }
        }

        @keyframes fillFade {
            0% {
                opacity: 0;
            }
            50% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }

        @keyframes pointFade {
            0% {
                opacity: 0;
            }
            70% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }
    </style>
    """

    # Insert the animation script before the closing body tag
    html = html.replace('</body>', f'{animation_script}</body>')

    return html


def get_holdings_by_type(user_id=None):
    """Fetch holdings aggregated by Security_Type over time from database, filtered by user if provided"""
    from .models import db, Position
    from sqlalchemy import func

    # Query to get market value by security type for each date, optionally filtered by user
    if user_id:
        positions = db.session.query(
            Position.Date,
            Position.Security_Type,
            func.sum(Position.Mkt_Val).label('total_value')
        ).filter(
            Position.Symbol != 'Account Total',
            Position.Security_Type.isnot(None),
            Position.Security_Type != '',
            Position.user_id == user_id
        ).group_by(Position.Date, Position.Security_Type).order_by(Position.Date, Position.Security_Type).all()
    else:
        positions = db.session.query(
            Position.Date,
            Position.Security_Type,
            func.sum(Position.Mkt_Val).label('total_value')
        ).filter(
            Position.Symbol != 'Account Total',
            Position.Security_Type.isnot(None),
            Position.Security_Type != ''
        ).group_by(Position.Date, Position.Security_Type).order_by(Position.Date, Position.Security_Type).all()

    # Convert to dataframe
    if positions:
        data = []
        for pos in positions:
            try:
                # Clean the total_value (sum of strings with $ and commas)
                if isinstance(pos.total_value, str):
                    cleaned_value = float(str(pos.total_value).replace('$', '').replace(',', ''))
                else:
                    cleaned_value = float(pos.total_value) if pos.total_value else 0
                data.append({
                    'Date': pos.Date,
                    'Security_Type': pos.Security_Type,
                    'total_value': cleaned_value
                })
            except (ValueError, TypeError):
                continue
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(columns=['Date', 'Security_Type', 'total_value'])

    # Return empty dataframe if no data
    if df.empty:
        return df

    # Convert to numeric and datetime
    df['total_value'] = pd.to_numeric(df['total_value'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Remove rows with null values or invalid dates
    df = df.dropna(subset=['Date', 'total_value'])

    # Sort by date
    df = df.sort_values('Date').reset_index(drop=True)

    return df

def create_holdings_by_type_graph(user_id=None):
    """Create an animated pie chart showing distribution of holdings by security type"""
    df = get_holdings_by_type(user_id)

    if df.empty:
        # Return empty graph if no data
        fig = go.Figure()
        fig.update_layout(
            title={
                'text': 'Holdings by Type - No Data Available',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='#F9F9F9', family='ClashDisplay'),
            },
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font=dict(color='#F9F9F9', family='ClashDisplay'),
        )
        return fig.to_html(
            include_plotlyjs='cdn',
            div_id='holdings-pie',
            config={'displayModeBar': False},
        )

    # Get the most recent date data
    latest_date = df['Date'].max()
    latest_data = df[df['Date'] == latest_date]

    # Color palette for different security types
    colors = {
        'Equity': "#FAEDCB",
        'Mutual Fund': '#C9E4DE',
        'ETFs & Closed End Funds': '#C6DEF1',
        'Cash and Money Market': '#DBCDF0',
        'Cryptocurrency': '#F2C6DE',
        '--': '#F7D9C4',
        'Other': '#7E8586'
    }

    # Prepare data for pie chart
    labels = latest_data['Security_Type'].tolist()
    values = latest_data['total_value'].tolist()
    pie_colors = [colors.get(label, f'hsl({(idx * 360 / len(labels))}, 100%, 50%)')
                for idx, label in enumerate(labels)]

    # Create figure with full data
    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=pie_colors),
            textposition='outside',
            textinfo='label+percent',
            textfont=dict(size=14, color='#293949', family='ClashDisplay', weight=500),
            hoverinfo='label+value+percent',
            pull=[0.02] * len(labels),
        )]
    )

    # Update layout
    fig.update_layout(
        title={
            'text': f'Holdings by Security Type (as of {latest_date.strftime("%m/%d/%Y")})',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=28, color='#F9F9F9', family='ClashDisplay', weight='bold' ),
        },
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#F9F9F9', family='ClashDisplay'),
        showlegend=True,
        xaxis=dict(domain=[0, 0.75]),
        yaxis=dict(domain=[0, 1]),
        legend=dict(
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            bgcolor='rgba(41, 57, 73, 0.7)',
            bordercolor='rgba(249, 249, 249, 0.2)',
            borderwidth=3
        ),
        margin=dict(l=20, r=250, t=60, b=10)
    )

    # Convert to HTML
    html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='holdings-pie',
        config={'displayModeBar': False, 'responsive': True}
    )

    # Add smooth CSS animation for pie chart
    animation_script = """
    <style>
        #holdings-pie {
            animation: chartFadeIn 0.6s ease-out forwards;
        }

        #holdings-pie .pie {
            animation: pieSpin 2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
            transform-origin: center;
            font-family: 'ClashDisplay', sans-serif;
        }

        #holdings-pie .slicepath {
            animation: sliceFade 1.8s ease-out 0.2s forwards;
            opacity: 0;
        }

        #holdings-pie text {
            opacity: 1;
            font-family: 'ClashDisplay', sans-serif;
            word-wrap: break-word;
            word-break: break-word;
            white-space: pre-wrap;
            max-width: 80px;
        }

        #holdings-pie .legendlayer text,
        #holdings-pie .legendlayer path {
            animation: legendFade 0.8s ease-out 1.4s forwards;
            opacity: 0;
            font-family: 'ClashDisplay', sans-serif;
        }

        #holdings-pie .legendlayer g {
            transform: translate(10px, 0);
        }

        #holdings-pie .legendlayer text {
            dy: 0.35em;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 150px;
            white-space: normal;
        }

        #holdings-pie .legendlayer {
            max-width: 180px;
            word-break: break-word;
        }

        #holdings-pie .hovertext {
            animation: none !important;
            opacity: 1 !important;
            font-family: 'ClashDisplay', sans-serif !important;
        }

        #holdings-pie .hovertext tspan {
            font-family: 'ClashDisplay', sans-serif !important;
        }

        @keyframes chartFadeIn {
            0% {
                opacity: 0;
                transform: translateY(30px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes pieSpin {
            0% {
                opacity: 0;
                transform: scale(0.3) rotateZ(-360deg);
            }
            40% {
                opacity: 1;
            }
            100% {
                opacity: 1;
                transform: scale(1) rotateZ(0deg);
            }
        }

        @keyframes sliceFade {
            0% {
                opacity: 0;
                filter: brightness(0.7);
            }
            100% {
                opacity: 1;
                filter: brightness(1);
            }
        }

        @keyframes textFade {
            0% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }

        @keyframes legendFade {
            0% {
                opacity: 0;
                transform: translateX(10px);
            }
            100% {
                opacity: 1;
                transform: translateX(0);
            }
        }
    </style>
    """

    # Insert the animation script before the closing body tag
    html = html.replace('</body>', f'{animation_script}</body>')

    return html

def create_DUMMY_animated_timeline_graph():
    """Create an animated line graph showing portfolio growth over time with smooth CSS animation"""
    df = get_FAKE_portfolio_timeline_data()

    # Create the complete figure with all data
    fig = go.Figure()

    # Add the main line trace with all data (no hover text)
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['portfolio_value'],
        mode='lines',
        line=dict(color='#293949', width=3, shape='spline', smoothing=1.3),
        fill='tozeroy',
        fillcolor='rgba(41, 57, 73, 0.1)',
        name='Portfolio Value',
        hoverinfo='skip'
    ))

    # Update layout with fixed axis ranges
    fig.update_layout(
        title={
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, color='#F9F9F9', family='ClashDisplay'),
        },
        xaxis=dict(
            title=dict(text='Date', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9'),
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            range=[df['Date'].min(), df['Date'].max()],
            showspikes=False
        ),
        yaxis=dict(
            title=dict(text='Portfolio Value ($)', font=dict(size=14, color='#F9F9F9', family='ClashDisplay')),
            tickfont=dict(color='#F9F9F9', family='ClashDisplay'),
            tickformat='$,.0f',
            gridcolor='rgba(255, 255, 255, 0.1)',
            showgrid=True,
            showticklabels=False,
            range=[0, df['portfolio_value'].max() * 1.1]
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color='#F9F9F9', family='ClashDisplay'),
        hovermode='closest'
    )

    # Convert to HTML with custom JavaScript for smooth animation
    html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='animated-timeline',
        config={'displayModeBar': False}
    )

    # Add custom JavaScript for smooth SVG path animation
    animation_script = """
    <style>
        #animated-timeline .scatterlayer path.js-line {
            stroke-dasharray: 3000;
            stroke-dashoffset: 3000;
            animation: dash 6s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer path.js-fill {
            opacity: 0;
            animation: fillFade 3s ease-in-out forwards;
        }

        #animated-timeline .scatterlayer .point {
            opacity: 0;
            animation: pointFade 3s ease-in-out forwards;
        }

        @keyframes dash {
            to {
                stroke-dashoffset: 0;
            }
        }

        @keyframes fillFade {
            0% {
                opacity: 0;
            }
            50% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }

        @keyframes pointFade {
            0% {
                opacity: 0;
            }
            70% {
                opacity: 0;
            }
            100% {
                opacity: 1;
            }
        }
    </style>
    """

    # Insert the animation script before the closing body tag
    html = html.replace('</body>', f'{animation_script}</body>')

    return html

