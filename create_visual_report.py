"""Create publication-sized PNG and SVG figures using Python."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'outputs/visual_report'
INK, BLUE, TEAL, GOLD = '#183348', '#3478b9', '#008577', '#d99232'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
    'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':INK,
    'text.color':INK,'axes.titlecolor':INK,'axes.edgecolor':'#ccd5dc',
    'grid.color':'#e3e9ed','axes.axisbelow':True,'savefig.facecolor':'white'})


def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=180,bbox_inches='tight')
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight')
    plt.close(fig)


def title(fig,heading,subtitle):
    fig.suptitle(heading,x=.07,y=.99,ha='left',fontsize=21,fontweight='bold')
    fig.text(.07,.90,subtitle,fontsize=11,color='#5b6d79')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p=pd.read_csv(ROOT/'outputs/improved/predictions.csv',parse_dates=['date'])
    f=pd.read_csv(ROOT/'outputs/improved/fold_metrics.csv')
    coverage=pd.read_csv(ROOT/'outputs/validation_review/coverage_by_group.csv',parse_dates=['date'])
    q=p[(p.DMA==2)&(p.location=='external')&(p.target=='median')&(p.fold==6)]
    wide=q.pivot(index='date',columns='model',values='predicted')
    actual=q.drop_duplicates('date').set_index('date').observed.sort_index()
    fig,ax=plt.subplots(2,1,figsize=(12,8),sharex=True,gridspec_kw={'height_ratios':[2,1]})
    title(fig,'Following daily demand','Area 2 · external meters · median target · 22 January–21 April 2015')
    ax[0].plot(actual.index,actual*1000,color=INK,lw=2,label='Observed')
    for name,label,color in [('previous_day','Yesterday baseline',GOLD),('fixed_history_ridge','History-only Ridge',TEAL)]:
        ax[0].plot(wide.index,wide[name]*1000,color=color,lw=1.5,alpha=.9,label=label)
    ax[0].set_ylabel('Median consumption (litres / meter / day)')
    ax[0].legend(ncol=3,loc='upper left',frameon=False,fontsize=10)
    error=1000*(wide.fixed_history_ridge-actual)
    ax[1].bar(wide.index,error,color=np.where(error>=0,BLUE,TEAL),width=.85)
    ax[1].axhline(0,color=INK,lw=.8); ax[1].set_ylabel('Ridge error (litres)\nPositive = too high')
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    for a in ax:a.grid(axis='y',alpha=.7)
    fig.subplots_adjust(top=.86,bottom=.10,hspace=.13)
    fig.text(.07,.025,'Daily predictions use prior observed demand; this is not a 90-day forecast issued at once.',fontsize=10)
    save(fig,'01_forecast_story')

    # Fold-level percentage changes reveal instability hidden by overall means.
    a=f[f.DMA==2].pivot(index=['location','target','fold'],columns='model',values='MAE')
    changes=(100*(a.fixed_past_weather_ridge/a.fixed_history_ridge-1)).unstack('fold')
    fig,ax=plt.subplots(figsize=(12,5.8))
    title(fig,'Does yesterday’s weather help consistently?','Area 2 · change in MAE relative to history-only Ridge · lower is better')
    bound=max(1,float(np.abs(changes.to_numpy()).max()))
    im=ax.imshow(changes,cmap='BrBG_r',norm=TwoSlopeNorm(vmin=-bound,vcenter=0,vmax=bound),aspect='auto')
    ax.set_yticks(range(len(changes)),[f'{x.title()} · {y}' for x,y in changes.index])
    ax.set_xticks(range(6),[f'Block {i}' for i in range(1,7)])
    for i in range(len(changes)):
        for j in range(6):ax.text(j,i,f'{changes.iloc[i,j]:+.1f}%',ha='center',va='center',fontsize=12,
            color='white' if abs(changes.iloc[i,j])>.65*bound else INK)
    fig.colorbar(im,ax=ax,pad=.025,label='MAE change (%)')
    fig.subplots_adjust(top=.81,left=.19,bottom=.15)
    fig.text(.07,.035,'Teal = improvement; brown = deterioration. Blocks are consecutive 90-day periods; no significance claim.',fontsize=10)
    save(fig,'02_weather_consistency')

    # Real measured absolute errors; targets remain separate.
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    title(fig,'Where prediction errors accumulate','Area 2 · external meters · six test blocks · errors in original target units')
    for ax,target in zip(axes,['mean','median']):
        s=p[(p.DMA==2)&(p.location=='external')&(p.target==target)]
        for model,label,color in [('previous_day','Yesterday',GOLD),('fixed_history_ridge','History Ridge',TEAL),('selected','Selected from earlier data',BLUE)]:
            z=s[s.model==model].sort_values('date')
            ax.plot(z.date,(z.predicted-z.observed).abs().cumsum()*1000,label=label,color=color,lw=2)
        ax.set_title(f'{target.title()} consumption target',fontsize=13)
        ax.set_ylabel('Cumulative absolute error (litres / meter)');ax.grid(axis='y')
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4));ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.tick_params(axis='x',rotation=25)
    axes[0].legend(frameon=False,fontsize=9)
    fig.subplots_adjust(top=.8,bottom=.20,wspace=.25)
    fig.text(.07,.025,'Lower curves are better. Mean and median are different tasks; panel scales differ. Selected models can change by block.',fontsize=10)
    save(fig,'03_error_accumulation')

    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
    title(fig,'The population being measured changes','Reporting meter records by area and location · no interpolation across missing participation')
    for ax,dma in zip(axes,[1,2]):
        for loc,color in [('external',BLUE),('internal',TEAL)]:
            s=coverage[(coverage.DMA==dma)&(coverage.meter_location==loc)]
            ax.fill_between(s.date,s['count'],alpha=.12,color=color)
            ax.plot(s.date,s['count'],color=color,label=loc.title(),lw=1.8)
        ax.set_ylabel(f'Area {dma}\nReporting records');ax.legend(loc='upper left',ncol=2,frameon=False)
        ax.grid(axis='y')
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig.subplots_adjust(top=.83,bottom=.13,hspace=.18)
    fig.text(.07,.025,'A change in the average can reflect who reports as well as how much water they use. Records are not unique households.',fontsize=10)
    save(fig,'04_coverage_story')

    # Association is descriptive; include medians and IQR, not confidence intervals.
    weather=pd.read_csv(ROOT/'data/raw/weather/haduk_yorkshire_daily.csv',parse_dates=['date'])
    s=coverage[(coverage.DMA==2)&(coverage.meter_location=='external')].merge(weather,on='date')
    s=s[s['count']>0].copy();s['temperature']=(s.tasmax+s.tasmin)/2
    s['bin']=pd.cut(s.temperature,np.arange(-10,31,5),right=False)
    fig,axes=plt.subplots(1,2,figsize=(12,6))
    title(fig,'Weather relationships are not forecasting proof','Area 2 · external meters · all reporting days · contemporaneous temperature')
    for ax,target in zip(axes,['mean','median']):
        ax.scatter(s.temperature,s[target]*1000,s=10,alpha=.18,color=BLUE,rasterized=True)
        grouped=s.groupby('bin',observed=True)
        for interval,g in grouped:
            if len(g)<10:continue
            low,mid,high=g[target].quantile([.25,.5,.75])*1000
            center=interval.mid
            ax.errorbar(center,mid,yerr=[[mid-low],[high-mid]],fmt='o',color=TEAL,capsize=5,lw=2)
            ax.annotate(f'n={len(g)}',(center,high),xytext=(0,7),textcoords='offset points',ha='center',fontsize=8)
        ax.set_title(f'Daily {target}',fontsize=13);ax.set_xlabel('Regional mean temperature (°C)')
        ax.set_ylabel('Consumption (litres / meter / day)');ax.grid(axis='y')
    fig.subplots_adjust(top=.8,bottom=.2,wspace=.25)
    fig.text(.07,.045,'Dots = individual days. Teal points = bin medians; bars = middle 50% of days, not confidence intervals.',fontsize=10)
    fig.text(.07,.018,'Bins with fewer than 10 days are omitted from summaries. Seasonality, coverage and anomalies can confound relationships.',fontsize=10)
    save(fig,'05_weather_relationship')

    print(f'Created five PNG/SVG figures in {OUT}')


if __name__=='__main__':main()

