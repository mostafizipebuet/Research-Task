"""Publication-oriented plots: vector PDF/SVG and 300-dpi PNG, no network or API."""
from pathlib import Path
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages
from .coding import SOURCE_STATUS, ALIGNMENT_STATUS

NAVY='#17324d';TEAL='#007f85';ORANGE='#c87928';GRAY='#d5dce3'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,
                     'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'stselab-v1',
                     'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold',
                     'axes.labelcolor':NAVY,'text.color':NAVY,'xtick.color':NAVY,'ytick.color':NAVY,
                     'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})

def save(fig, folder, stem):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    fig.savefig(folder/(stem+'.png'),dpi=300,bbox_inches='tight')
    fig.savefig(folder/(stem+'.pdf'),bbox_inches='tight',metadata={'Creator':'STSELab research analysis package','CreationDate':None,'ModDate':None})
    fig.savefig(folder/(stem+'.svg'),bbox_inches='tight',metadata={'Date':None,'Creator':'STSELab research analysis package'})
    plt.close(fig)

def note(fig,text):
    fig.text(.02,.015,text,ha='left',va='bottom',fontsize=8,color='#485b6c',wrap=True)

def figures(metrics,annotations,audit,codebook,criteria,reference,folder,mode):
    req=[r['requirement_id'] for r in reference['requirements']]
    crit=[r['criterion_id'] for r in criteria]
    labels={r['reason_id']:r['label'] for r in codebook}
    n=audit['n_runs'];status='REVIEWED' if mode=='final' else 'PROVISIONAL LABELS'
    captions={}
    fig,ax=plt.subplots(figsize=(10.2,6.1));ax.set_xlim(0,10);ax.set_ylim(0,6);ax.axis('off')
    boxes=[(.3,3.5,'1  Preserve and audit',f'{n} runs · {audit["n_requirements"]} requirements\nJSON schema, IDs and source hashes'),
           (3.6,3.5,'2  Preserve each flag','Original text + stable record ID\nComplete unflagged opportunity grid'),
           (6.9,3.5,'3  Propose reason labels','Explicit multi-label codebook\nMatched text; unresolved cases kept'),
           (6.9,1.0,'4  Review interpretations','Check labels, evidence and fit\nRecord reviewer, note and source'),
           (3.6,1.0,'5  Measure patterns','Frequency · stability · overlap\nFixed-set uncertainty across runs'),
           (.3,1.0,'6  Report with evidence','Figures, tables and case examples\nLimitations and reproducible files')]
    for x,y,title,body in boxes:
        patch=FancyBboxPatch((x,y),2.8,1.45,boxstyle='round,pad=0.10',facecolor='#eef4f7',edgecolor=TEAL,linewidth=1.4)
        ax.add_patch(patch);ax.text(x+.14,y+1.1,title,fontsize=10.5,fontweight='bold');ax.text(x+.14,y+.72,body,fontsize=8.2,va='top',linespacing=1.6)
    arrows=[((3.2,4.2),(3.48,4.2)),((6.5,4.2),(6.78,4.2)),((8.3,3.35),(8.3,2.6)),((6.78,1.72),(6.5,1.72)),((3.48,1.72),(3.2,1.72))]
    for a,b in arrows:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,color=NAVY,linewidth=1.3))
    ax.set_title('From raw explanations to traceable research findings',loc='left',pad=12)
    note(fig,'Human interpretation is a recorded research step. Rule matches propose labels; they do not establish requirement defects.')
    save(fig,folder,'F01_analysis_workflow');captions['F01_analysis_workflow']='Analysis design. Original data and proposed labels are retained separately from reviewed interpretations.'

    matrix=metrics['flag_frequency'].pivot(index='requirement_id',columns='criterion_id',values='flags').reindex(index=req,columns=crit)
    fig,ax=plt.subplots(figsize=(8.9,7.1));im=ax.imshow(matrix.to_numpy(),cmap='Blues',vmin=0,vmax=n,aspect='auto')
    ax.set_xticks(range(len(crit)),[f'{c}\n{next(x["name"] for x in criteria if x["criterion_id"]==c)}' for c in crit],fontsize=8)
    ax.set_yticks(range(len(req)),req);ax.set_xlabel('Quality criterion');ax.set_ylabel('Requirement')
    for i in range(len(req)):
        for j in range(len(crit)):
            v=int(matrix.iloc[i,j]);ax.text(j,i,str(v),ha='center',va='center',fontsize=9,color='white' if v>n*.57 else NAVY)
    cb=fig.colorbar(im,ax=ax,fraction=.035,pad=.03);cb.set_label(f'Flagged runs out of {n}')
    ax.set_title(f'How often each criterion was flagged across {n} runs',loc='left',pad=18)
    fig.subplots_adjust(bottom=.16,left=.12,right=.86,top=.9)
    note(fig,'Exact descriptive counts. A flag is an LLM judgment; an unflagged cell is not a verified pass. Wilson intervals are in the CSV table.')
    save(fig,folder,'F02_flag_frequency_heatmap');captions['F02_flag_frequency_heatmap']=f'Flag counts for all {len(req)*len(crit)} requirement–criterion pairs. Every cell has denominator {n} runs; zero cells are retained.'

    counts=metrics['reason_assignments'].groupby('reason_id').size().sort_values(ascending=False).head(12).sort_values()
    fig,ax=plt.subplots(figsize=(10.8,7.0))
    if len(counts):
        y=np.arange(len(counts));ax.barh(y,counts.values,color=TEAL,height=.65)
        ax.set_yticks(y,[f'{x}  {labels[x]}' for x in counts.index],fontsize=9)
        for i,v in enumerate(counts.values):ax.text(v+max(counts.max()*.015,1),i,f'{v:,}  ({v/len(annotations):.1%})',va='center',fontsize=8)
        ax.set_xlim(0,counts.max()*1.25)
    else:ax.text(.5,.5,'No reasons have been coded.',transform=ax.transAxes,ha='center')
    ax.set_xlabel('Flag explanations containing the reason');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    ax.set_title('Most frequent reasons across flag explanations',loc='left',pad=22)
    fig.text(.02,.94,status,fontsize=8,color=ORANGE,fontweight='bold')
    fig.subplots_adjust(left=.39,right=.97,bottom=.14,top=.88)
    note(fig,f'Percentages use {len(annotations):,} flag explanations. Multiple reasons per explanation are allowed, so percentages can sum above 100%.')
    save(fig,folder,'F03_reason_prevalence');captions['F03_reason_prevalence']=f'Top 12 coded reasons by number of flag explanations. {status}. Each flag contributes at most once to each reason.'

    stab=metrics['run_stability'];fig,axs=plt.subplots(1,2,figsize=(11.8,5.8),sharey=True)
    for j,(column,title) in enumerate([('flag_agreement','A  Exact flag agreement'),('mean_jaccard_both_positive','B  Reason similarity when both runs flag')]):
        ax=axs[j]
        for i,c in enumerate(crit):
            g=stab[(stab.criterion_id==c)&(stab.flagged_runs>0)].copy()
            if j==1:g=g[g.pairs_both_positive>0]
            vals=g[column].dropna().to_numpy()
            jitter=np.linspace(-.20,.20,len(vals)) if len(vals)>1 else np.array([0.])
            if len(vals):
                ax.scatter(vals,np.full(len(vals),i)+jitter,s=28,color=TEAL if j else NAVY,alpha=.75,zorder=3)
                med=float(np.median(vals));ax.plot([med,med],[i-.28,i+.28],color=ORANGE,lw=2.2,zorder=4)
        ax.set_xlim(-.03,1.03);ax.set_xticks([0,.25,.5,.75,1]);ax.grid(axis='x',alpha=.2);ax.set_title(title,fontsize=10.5,loc='left');ax.set_xlabel('Agreement / similarity (0 to 1)')
    axs[0].set_yticks(range(len(crit)),crit);axs[0].invert_yaxis();axs[0].set_ylabel('Criterion')
    fig.suptitle('Agreement across repeated runs has two different meanings',x=.02,ha='left',fontsize=13,fontweight='bold')
    fig.subplots_adjust(left=.09,right=.97,bottom=.21,top=.82,wspace=.12)
    note(fig,f'Each dot = one requirement; orange ticks = medians. Zero-flag pairs omitted. Reason results: {status.lower()}.\nReason Jaccard excludes unresolved sets and requires both runs to flag. Run pairs are dependent; these are descriptive summaries.')
    save(fig,folder,'F04_run_consistency');captions['F04_run_consistency']='Flag agreement includes both-present and both-absent decisions. Conditional Jaccard compares known reason sets only when both runs flag. Dots represent requirements, not independent run pairs.'

    matrix=metrics['reason_by_criterion'].pivot(index='reason_id',columns='criterion_id',values='flag_explanations_with_reason').reindex(columns=crit).fillna(0)
    active=matrix[(matrix>0).sum(axis=1)>=2]
    active=active.loc[active.sum(axis=1).sort_values(ascending=False).index]
    fig,ax=plt.subplots(figsize=(10.5,max(4.3,len(active)*.43+2.3)))
    if len(active):
        frac=active.div(active.sum(axis=1),axis=0)
        im=ax.imshow(frac,cmap='YlGnBu',vmin=0,vmax=1,aspect='auto')
        ax.set_yticks(range(len(active)),[f'{c}  {labels[c]}' for c in active.index],fontsize=9)
        ax.set_xticks(range(len(crit)),crit)
        for i in range(len(active)):
            for j in range(len(crit)):
                ax.text(j,i,str(int(active.iloc[i,j])),ha='center',va='center',fontsize=9,color='white' if frac.iloc[i,j]>.55 else NAVY)
        cb=fig.colorbar(im,ax=ax,fraction=.035,pad=.03);cb.set_label('Share of this reason assigned to each criterion')
    else:ax.text(.5,.5,'No reason occurs under multiple criteria.',transform=ax.transAxes,ha='center')
    ax.set_xlabel('LLM-assigned criterion');ax.set_title('Reasons that appear under multiple criteria',loc='left',pad=24)
    fig.subplots_adjust(left=.40,right=.86,bottom=.16,top=.88)
    note(fig,f'{status}. Cell labels = flag counts; colors = row shares. Shared reasons can reflect legitimate overlap; this alone does not prove criterion misuse.')
    save(fig,folder,'F05_cross_criterion_reasons');captions['F05_cross_criterion_reasons']='Only reasons observed under at least two criteria are shown. Cell counts retain each flag; the color scale normalizes within reason. Consult within-requirement overlap tables before interpreting differences.'

    fig,axs=plt.subplots(1,2,figsize=(12.0,5.9),sharey=True)
    for ax,field,states,title in [(axs[0],'source_status',SOURCE_STATUS,'A  Evidence relative to supplied sources'),(axs[1],'alignment_status',ALIGNMENT_STATUS,'B  Fit to assigned criterion')]:
        left=np.zeros(len(crit));colors=[GRAY,TEAL,'#e5ad5c','#ba4d40','#67788e']
        for state,color in zip(states,colors):
            vals=[]
            for c in crit:
                g=annotations[annotations.criterion_id==c];vals.append(float(g[field].eq(state).mean()) if len(g) else 0)
            vals=np.array(vals);ax.barh(range(len(crit)),vals,left=left,color=color,label=state.replace('_',' '),height=.65);left+=vals
        ax.set_title(title,loc='left',fontsize=10.5);ax.set_xlim(0,1);ax.set_xticks([0,.5,1],['0%','50%','100%']);ax.set_xlabel('Share of flag explanations');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=2,fontsize=8,frameon=False)
    axs[0].set_yticks(range(len(crit)),crit);axs[0].invert_yaxis();axs[0].set_ylabel('Criterion')
    complete=int(((annotations.source_status!='pending')&(annotations.alignment_status!='pending')).sum())
    fig.suptitle(f'Interpretation review: {complete:,} of {len(annotations):,} flags assessed on both dimensions',x=.02,ha='left',fontsize=13,fontweight='bold')
    fig.subplots_adjust(left=.08,right=.98,bottom=.3,top=.83,wspace=.1)
    note(fig,'Pending remains visible. The software never converts a regex match into an expert judgment or a confirmed requirement defect.')
    save(fig,folder,'F06_evidence_and_alignment');captions['F06_evidence_and_alignment']='Review coverage and reviewer-entered judgments. Pending means no judgment has been entered. The initial package has no human-reviewed evidence or criterion-fit ratings.'
    return captions

def scientific_tables_pdf(path, frames):
    """A compact, multipage table book; full detail stays in the CSV/HTML tables."""
    with PdfPages(path,metadata={'Title':'STSELab scientific summary tables','CreationDate':None,'ModDate':None}) as pdf:
        page_no=0
        for title,df,widths,wraps,per_page,caption in frames:
            df=df.fillna('')
            for start in range(0,max(len(df),1),per_page):
                page_no+=1;chunk=df.iloc[start:start+per_page]
                fig,ax=plt.subplots(figsize=(11.7,8.3));ax.axis('off')
                fig.text(.045,.94,title,fontsize=15,fontweight='bold')
                fig.text(.045,.9,'Rows '+str(start+1)+'–'+str(min(start+per_page,len(df)))+' of '+str(len(df)),fontsize=9,color='#536576')
                cells=[]
                for vals in chunk.itertuples(index=False,name=None):
                    cells.append(['\n'.join(textwrap.wrap(str(v),width=wraps[j],break_long_words=True)) for j,v in enumerate(vals)])
                if not cells:cells=[['No observations']+['']*(len(df.columns)-1)]
                table=ax.table(cellText=cells,colLabels=[str(c) for c in df.columns],colWidths=widths,cellLoc='left',loc='upper left',bbox=[.01,.10,.98,.78])
                table.auto_set_font_size(False);table.set_fontsize(8.3)
                lines=[max(x.count('\n')+1 for x in row) for row in cells]
                unit=.72/(sum(lines)+len(lines)*.5+2)
                for (i,j),cell in table.get_celld().items():
                    cell.set_edgecolor('#c9d5df');cell.set_linewidth(.45);cell.PAD=.08
                    if i==0:cell.set_facecolor(NAVY);cell.get_text().set_color('white');cell.get_text().set_fontweight('bold');cell.set_height(unit*2)
                    else:cell.set_facecolor('#f1f5f8' if i%2 else 'white');cell.set_height(unit*(lines[i-1]+.5))
                fig.text(.045,.055,'\n'.join(textwrap.wrap(caption,145)),fontsize=8,color='#536576',va='bottom')
                fig.text(.96,.025,str(page_no),ha='right',fontsize=8)
                pdf.savefig(fig,bbox_inches=None);plt.close(fig)
