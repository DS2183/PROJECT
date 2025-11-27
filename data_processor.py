"""Data processing utilities for various data sources and formats."""
import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
import requests
import httpx
from bs4 import BeautifulSoup
import pandas as pd
from pypdf import PdfReader
from PIL import Image
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio

logger = logging.getLogger(__name__)

class DataProcessor:
    """Handle various data processing tasks."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.async_client = httpx.AsyncClient(headers=self.session.headers, timeout=30.0)

    async def close(self):
        """Close async resources."""
        await self.async_client.aclose()
    
    def download_file(self, url: str, headers: Optional[Dict] = None) -> bytes:
        """
        Download a file from a URL.
        
        Args:
            url: URL to download from
            headers: Optional custom headers
            
        Returns:
            File content as bytes
        """
        logger.info(f"Downloading file from {url}")
        response = self.session.get(url, headers=headers or {}, timeout=30)
        response.raise_for_status()
        return response.content

    async def download_file_async(self, url: str, headers: Optional[Dict] = None) -> bytes:
        """Async version of download_file."""
        logger.info(f"Downloading file async from {url}")
        response = await self.async_client.get(url, headers=headers or {})
        response.raise_for_status()
        return response.content
    
    def scrape_website(self, url: str, headers: Optional[Dict] = None) -> str:
        """
        Scrape text content from a website.
        
        Args:
            url: URL to scrape
            headers: Optional custom headers
            
        Returns:
            Extracted text content
        """
        logger.info(f"Scraping website {url}")
        response = self.session.get(url, headers=headers or {}, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text(separator=' ', strip=True)

    async def scrape_website_async(self, url: str, headers: Optional[Dict] = None) -> str:
        """Async version of scrape_website."""
        logger.info(f"Scraping website async {url}")
        response = await self.async_client.get(url, headers=headers or {})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
            
        return soup.get_text(separator=' ', strip=True)
    
    def parse_pdf(self, content: bytes, page: Optional[int] = None) -> str:
        """
        Extract text from PDF content.
        
        Args:
            content: PDF file content
            page: Optional page number (0-indexed) to extract from
            
        Returns:
            Extracted text
        """
        logger.info(f"Parsing PDF content, page: {page}")
        reader = PdfReader(io.BytesIO(content))
        
        if page is not None:
            if 0 <= page < len(reader.pages):
                return reader.pages[page].extract_text()
            else:
                logger.warning(f"Page {page} out of range (0-{len(reader.pages)-1})")
                return ""
        
        return "\n".join([p.extract_text() for p in reader.pages])

    def parse_csv(self, content: bytes) -> pd.DataFrame:
        """
        Parse CSV content into DataFrame.
        
        Args:
            content: CSV file content
            
        Returns:
            DataFrame
        """
        logger.info("Parsing CSV content")
        return pd.read_csv(io.BytesIO(content))

    def parse_excel(self, content: bytes, sheet_name: Union[str, int] = 0) -> pd.DataFrame:
        """Parse Excel content into DataFrame."""
        logger.info(f"Parsing Excel content, sheet: {sheet_name}")
        return pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
    
    def parse_json(self, content: bytes) -> Any:
        """Parse JSON content."""
        logger.info("Parsing JSON content")
        return pd.read_json(io.BytesIO(content))
    
    def create_chart(
        self,
        data: pd.DataFrame,
        chart_type: str = "bar",
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        title: str = "Chart"
    ) -> str:
        """
        Create a chart and return as base64 encoded image.
        
        Args:
            data: DataFrame with data to plot
            chart_type: Type of chart (bar, line, scatter, pie)
            x_col: Column for x-axis
            y_col: Column for y-axis
            title: Chart title
            
        Returns:
            Base64 encoded image string
        """
        logger.info(f"Creating {chart_type} chart")
        
        if data.empty:
            logger.warning("Empty dataframe, cannot create chart")
            return ""
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        try:
            if chart_type == "bar":
                data.plot(kind='bar', x=x_col, y=y_col, ax=ax)
            elif chart_type == "line":
                data.plot(kind='line', x=x_col, y=y_col, ax=ax)
            elif chart_type == "scatter":
                data.plot(kind='scatter', x=x_col, y=y_col, ax=ax)
            elif chart_type == "pie":
                data.plot(kind='pie', y=y_col, ax=ax)
            
            ax.set_title(title)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            plt.close()
            return ""
    
    def create_plotly_chart(
        self,
        data: pd.DataFrame,
        chart_type: str = "bar",
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        title: str = "Chart"
    ) -> str:
        """
        Create an interactive Plotly chart and return as base64 encoded image.
        
        Args:
            data: DataFrame with data to plot
            chart_type: Type of chart
            x_col: Column for x-axis
            y_col: Column for y-axis
            title: Chart title
            
        Returns:
            Base64 encoded image string
        """
        logger.info(f"Creating Plotly {chart_type} chart")
        
        if chart_type == "bar":
            fig = go.Figure(data=[go.Bar(x=data[x_col], y=data[y_col])])
        elif chart_type == "line":
            fig = go.Figure(data=[go.Scatter(x=data[x_col], y=data[y_col], mode='lines')])
        elif chart_type == "scatter":
            fig = go.Figure(data=[go.Scatter(x=data[x_col], y=data[y_col], mode='markers')])
        else:
            fig = go.Figure(data=[go.Bar(x=data[x_col], y=data[y_col])])
        
        fig.update_layout(title=title)
        
        # Convert to base64
        img_bytes = pio.to_image(fig, format='png', width=1000, height=600)
        image_base64 = base64.b64encode(img_bytes).decode()
        
        return f"data:image/png;base64,{image_base64}"
    
    def encode_file_to_base64(self, content: bytes) -> str:
        """
        Encode file content to base64 data URI.
        
        Args:
            content: File content as bytes
            
        Returns:
            Base64 encoded data URI
        """
        return f"data:application/octet-stream;base64,{base64.b64encode(content).decode()}"
