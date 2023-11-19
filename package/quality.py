import os 
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import stats


def print_quality_index(steps_lim_full, seg_lim, output):
    """Compute the quality index of the trial gait events detection (between 0 and 100) and produce a picture of the number surrounded by an appropriately colored circle. 
    Add quality index formula ? 

    Parameters
    ----------
        steps_lim_full {dataframe} -- pandas dataframe with all the detected gait events
        seg_lim {dataframe} -- pandas dataframe with phases events 
        output {str} -- folder path for output fig

    Returns
    -------
        qi {int} -- corrected quality index 
        steps_lim_corrected {dataframe} -- pandas dataframe with gait events after elimination of the extra trial steps
    """

    qi_raw = compute_quality_index(steps_lim_full, seg_lim)
    path_raw = os.path.join(output, "quality_index_raw.svg")
    plot_quality_index(qi_raw, path_raw)
  
    steps_lim_corrected, seg_lim_corrected = correct_steps_lim(steps_lim_full, seg_lim)
  
    qi_corrected = compute_quality_index(steps_lim_corrected, seg_lim_corrected)
    path_corrected = os.path.join(output, "quality_index_corrected.svg")
    plot_quality_index(qi_corrected, path_corrected)
  
    return qi_corrected, steps_lim_corrected, seg_lim_corrected


def plot_quality_index(qi, path):
    """Compute the quality index of the trial gait events detection (between 0 and 100) and produce a picture of the number surrounded by an appropriately colored circle. 
    Add quality index formula ? 

    Parameters
    ----------
        qi {int} -- quality index 
        path {str} -- file path for output fig
    """
  
    # plot qi
    max_qi=100
    xval = np.arange(0, 2*np.pi*(.05+0.90*(qi/max_qi)), 0.01)
    colormap = plt.get_cmap("RdYlGn")
    norm = mpl.colors.Normalize(0.0, 2*np.pi)
    f, ax = plt.subplots(nrows=1, ncols=1, figsize=(4,4),subplot_kw=dict(projection='polar'))
    #Scatter version
    yval = np.ones_like(xval)
    ax.scatter(xval, yval, c=xval, s=300, cmap=colormap, norm=norm, linewidths=0)
  
    ax.set_axis_off()
    ax.set_ylim(0,1.5)
    if qi<10:
        ax.annotate(qi,xy=( 1.25*np.pi, .3),color=colormap(.05+0.90*(qi/max_qi)),fontsize=50)
    else :
        ax.annotate(qi,xy=( 1.18*np.pi, .5),color=colormap(.05+0.90*(qi/max_qi)),fontsize=50)
  
    plt.savefig(path, dpi=80,
                    transparent=True, bbox_inches="tight")


def compute_quality_index(steps_lim, seg_lim):
  """Compute the quality index of the trial gait events detection (between 0 and 100)
  Add quality index formula ? 

    Parameters
    ----------
        steps_lim {dataframe} -- pandas dataframe with gait events
        seg_lim {dataframe} -- pandas dataframe with phases events 

    Returns
    -------
        qi {int} -- quality index 
    """
  
  # estimation of stride alternation
  steps_lim_sort = steps_lim.sort_values(by = ['HS', 'TO'])
  alt_go = steps_lim_sort[steps_lim_sort['HS'] < int(seg_lim[1])]['Foot'].tolist()
  alt_back = steps_lim_sort[steps_lim_sort['HS'] > int(seg_lim[2])]['Foot'].tolist()
  i = 0
  for k in range(len(alt_go)-1):
      i = i + abs(alt_go[k+1]-alt_go[k])
  for k in range(len(alt_back)-1):
      i = i + abs(alt_back[k+1]-alt_back[k])
  qi = round(100*i/(len(alt_go) + len(alt_back)-2), 4)

  return (len(alt_back)
    

def correct_steps_lim(steps_lim, seg_lim):
  """Correction of the steps_lim dataframe. U-turn steps 

    Parameters
    ----------
        steps_lim {dataframe} -- pandas dataframe with gait events
        seg_lim {dataframe} -- pandas dataframe with phases events 

    Returns
    -------
        qi {int} -- quality index 
    """
  
  # estimation of the start and end time samples for the trial to compute seg_lim_corrected
  start, end = get_bornes(steps_lim, seg_lim)
  seg_lim_corrected = [start, seg_lim[1], seg_lim[2], end]

  # suppression des pas du demi-tour et des pas en dehors des limites précédement estimées
  correct = []
  for i in range(len(steps_lim)):
      if inside([steps_lim["HS"][i], steps_lim["TO"][i]], seg_lim_corrected):
          correct.append(1)
      else:
          correct.append(0)
      
  steps_lim_corrected = steps_lim.copy()
  steps_lim_corrected["Correct"] = correct
    
  return steps_lim_corrected, seg_lim_corrected


def get_bornes(steps_lim, seg_lim):
  """Find start and end time sample for the trial. The beginning corresponds to the Toe-Off of the first step after deleting the steps outside the trial. 
  The end corresponds to the Heel-Strike of the last step after deleting the steps outside the trial. 

    Parameters
    ----------
        steps_lim {dataframe} -- pandas dataframe with gait events
        seg_lim {dataframe} -- pandas dataframe with phases events 

    Returns
    -------
        start, end {int, int} -- time samples corresponding to the estimated start and end for the trial. 
    """
  
  start = np.Inf
  end = 0

  for foot in [0, 1]:

      # estimation of average stride duration
      steps_lim_f = steps_lim[steps_lim["Foot"] == foot]
      hs_f = steps_lim_f["HS"].tolist()
      hs_t = []
    
      for i in range(len(hs_f) - 1):  # for outlier search, we exclude the first and last steps 
          hs_t.append(hs_f[i + 1] - hs_f[i])  # hs_t contains all stride durations 
      hs_t = rmoutliers(hs_t)  # function for eliminating outliers (start, U-turn, end)
      strT = np.median(hs_t)  # estimation of average stride duration 
      to_f = steps_lim_f["TO"].tolist()  # for the side under consideration, this vector contains all Toe-Off dates

      # find the estimated start of the trial: start from the beginning and work forward
      find_start = 0
      i = 0
      while not find_start:
          if abs(to_f[i] - to_f[i + 2]) < 3 * strT:  # if the time between strides i and i+2 (expected time 2*strT) is less than 3*strT, the test is considered to have started
              find_start = 1
              if to_f[i] < start:
                  start = to_f[i]
          else:  # if the previous condition is not met, stride i is probably an outlier before the trial begins.
              i = i + 1

      # search for the estimated end of the trial: start from the end and work backwards
      find_end = 0
      i = np.argmin(abs(np.array(hs_f) - (seg_lim[2] + 0.5 * (seg_lim[2] - start))))

      while (not find_end) & (i < len(hs_f)):
          if abs(hs_f[i] - hs_f[i - 2]) < 3 * strT:  # si la durée entre les strides i et i+2 (durée attendue 2*strT) est inférieure 3*strT, on considère qu'on est encore dans l'épreuve
              if i == len(hs_f) - 1:
                  find_end = 1
                  if hs_f[i] > end:
                      end = hs_f[i]
              else:
                  i = i + 1
          else:  # if the previous condition is not met, stride i is probably an outlier after the end of the trial. We therefore set the end of the trial at i-1
              find_end = 1
              if hs_f[i - 1] > end:
                  end = hs_f[i - 1]

  return start, end


def inside(liste, seg_lim):
    out = 0
    in_go = 0
    in_back = 0
    for x in liste:
        if x < seg_lim[0]:
            out = 1
        else:
            if (x > seg_lim[1]) and (x < seg_lim[2]):
                out = 1
            else:
                if x > seg_lim[3]:
                    out = 1
                else:
                    if (x <= seg_lim[1]) and (x >= seg_lim[0]):
                        in_go = 1
                    else:
                        if (x <= seg_lim[3]) and (x >= seg_lim[2]):
                            in_go = 1

    if out + in_go + in_back == 0:
        return 0
    else:
        if out == 1:
            return 0
        else:
            if in_go + in_back == 2:
                return 0
            else:
                if in_go + in_back == 1:
                    return 1


def rmoutliers(vec, limite=2):
    # print("Avant :", vec)
    z = np.abs(stats.zscore(vec))
    vec1 = []
    for i in range(len(vec)):
        if z[i] < limite:  # La valeur à partir de laquelle on peut supprimer les données peut varier
            vec1.append(vec[i])
    # print("Après :", vec1)
    return vec1
