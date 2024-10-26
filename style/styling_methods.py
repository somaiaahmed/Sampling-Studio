import pyqtgraph as pg
def style_plot_widget(plot_widget):
    plot_widget.setBackground('#FFFFFF')
    plot_widget.getAxis('left').setPen(pg.mkPen(color='gray'))
    # plot_widget.getAxis('bottom').setPen(pg.mkPen(color='gray'))
    plot_widget.defaultPen = pg.mkPen(color='b', width=3)
    # plot_widget.showGrid(x=True, y=True, alpha=0.3)
    plot_widget.setStyleSheet("""
        border: 2px solid #FFFFFF;    
        border-radius: 20px;            
    """)
    
