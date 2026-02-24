from GML import *

def ratio_list(node,max_depth,denominator_number=1,print_list=False):
    """
    Return a list of frequency ratios used in a GML tree
    For the ratios, the denominator_number is 0 for smallest frequency or 1 for second smallest frequency
    """
    freq_list=node.frequency_list(max_depth)
    #print(freq_list)
    ratio_list=[]
    for items in freq_list:
        ratio_list.append(items/freq_list[denominator_number])
    if(print_list):
        print("Frequency ratio List: ",ratio_list)
    return ratio_list

def adjacient_ratio_list(node,max_depth,print_list=False):
    ratio_list=node.adjacient_ratio_list(max_depth)
    if(print_list):
        print("Adjacent frequency ratio List: ",ratio_list)
    return ratio_list
