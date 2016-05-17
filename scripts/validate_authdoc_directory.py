import os
import sys
import csv
import time
from load_conf import auth_dir, log_dir

#auth_dir = r'concepts\authority_files'

def parse_auth_doc(auth_doc_reader):
    '''basic checking and parsing of file'''

    labelerror = False
    typeerror = False
    conceptids = []
    parentconceptids = []
    ct = 0

    for row in auth_doc_reader:
        ct+=1
        conceptids.append(row[0])
        parentconceptids.append(row[3])
        if row[1] == '':
            labelerror = "error in PrefLabel column"
        if not row[4] in ("Index","Collector"):
            typeerror = "error in ConceptType column"

    return (conceptids,parentconceptids,ct,(labelerror,typeerror))

def check_auth_doc(conceptids, parentconceptids, filename):
    '''check conceptids, ParentConceptids:
1. all conceptids must be unique across all auth docs
2. ParentConceptids must equal the file name or a conceptid'''

    cid_errors = []
    pcid_errors = []

    # this didn't seem to catch a mistyped name of the file name
    for pcid in parentconceptids:
        if not pcid in conceptids and not pcid == filename:
            pcid_errors.append(pcid)

    for i in conceptids:
        if conceptids.count(i)>1:
            cid_errors.append(i)
        
    return (cid_errors, pcid_errors)

def check_all_cids(cid_list,auth_doc_dir):
    '''find any non-unique cids in input list, return which auth docs use them'''

    repeats = set([i for i in cid_list if cid_list.count(i)>1])
    if len(repeats) == 0:
        return False
    
    full_dict = {i:[] for i in repeats}
    for f in os.listdir(auth_doc_dir):

        if not f.endswith("AUTHORITY_DOCUMENT.csv"):
            continue

        f_path = os.path.join(auth_doc_dir,f)
        with open(f_path, "rb") as read:
            reader = csv.reader(read, delimiter=",")
            reader.next()
            cids = set(parse_auth_doc(reader)[0])
            for cid in cids:
                if cid in full_dict.keys():
                    full_dict[cid].append(f)

    repeat_dict = {i:v for i,v in full_dict.iteritems() if len(v)>1}
    return repeat_dict

def check_values_file(input_file, conceptids):
    '''makes sure the input file uses valid conceptids'''

    with open(input_file, "rb") as readthis:
        reader = csv.reader(readthis, delimiter=",")
        reader.next()
        v_cids = [r[0] for r in reader]
        
    bad_ids = [i for i in set(v_cids) if not i in conceptids]

    return bad_ids             
                       
def process_auth_docs(auth_doc_dir,log_dir):
    '''validate all auth docs in input directory'''

    logfile = os.path.join(log_dir,"_validation.log")
    msg_dict = {}
    with open(logfile, "w") as log:

        all_conceptids = []
        doc_count = 0
        vdoc_count = 0
        error_files = []

        for f in os.listdir(auth_doc_dir):

            #filter everything but the authority documents
            if not f.endswith("AUTHORITY_DOCUMENT.csv"):
                continue

            msg_dict[f] = {}
            doc_count+=1

            v_file_name = f.replace("csv","values.csv")
            v_file_path = os.path.join(auth_doc_dir,v_file_name)
            v_file = os.path.isfile(v_file_path)
            msg_dict[f]['values_file'] = v_file

            f_path = os.path.join(auth_doc_dir,f)
            with open(f_path, "rb") as read:
                
                reader = csv.reader(read, delimiter=",")
                reader.next()
                cids, pcids, row_ct, col_errors = parse_auth_doc(reader)
                all_conceptids+=cids
                cid_errors,pcid_errors = check_auth_doc(cids, pcids, f)

                msg_dict[f]['count'] = len(cids)

                v_errors = []
                if v_file:
                    vdoc_count+=1
                    v_errors = check_values_file(v_file_path,cids)
                    
                msg_dict[f]['errors'] = (v_errors,cid_errors,pcid_errors)

                if len(cid_errors) == 0 and len(pcid_errors) == 0 and len(v_errors) == 0:
                    msg_dict[f]['error_msg'] = "ALL OK"
                else:
                    msg_dict[f]['error_msg'] = "ERRORS:"
                    error_files.append(f)

        print >> log, "~~~SUMMARY~~~\n"
        print >> log, doc_count, "auth docs found"
        print >> log, vdoc_count, "have values docs"
        print >> log, len(error_files), "have errors"
        if len(error_files) > 0:
            for ef in error_files:
                print >> log, " ",ef

        repeat_dict = check_all_cids(all_conceptids,auth_doc_dir)
        if repeat_dict:
            print >> log, "system-wide conceptid problems:"
            for k, v in repeat_dict.iteritems():
                print >> log, k
        else:
            print >> log, "\nsystem-wide, conceptids are unique"

        print >> log, "\n~~~ERROR DETAILS~~~"
        files = msg_dict.keys()
        files.sort()
        for doc in files:
            if msg_dict[doc]['error_msg'] == "ERRORS:":
                
                msg1 = \
'''
{0}
  {1} concept(s)
  has values file: {2}'''.format(doc, msg_dict[doc]['count'],
                    msg_dict[doc]['values_file'])
                print >> log, msg1
                verrors, cid_errors, pcid_errors = msg_dict[doc]['errors']
                print >> log, "  ERRORS:"
                if len(verrors) > 0:
                    print >> log, "    in values file:\n      {0}".format("\n      ".join(verrors))
                if len(cid_errors) > 0:
                    print >> log, "    in conceptids:\n      {0}".format("\n      ".join(cid_errors))
                if len(pcid_errors) > 0:
                    print >> log, "    in parentconceptids:\n      {0}".format("\n      ".join(pcid_errors))
                
    return logfile
    

output = process_auth_docs(auth_dir,log_dir)
try:
    os.startfile(output)
except:
    pass
print ("output stored in log:\n{0}".format(output))
