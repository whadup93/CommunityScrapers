import json
import sys
import os

try:
    import py_common.graphql as graphql
    import py_common.log as log
except ModuleNotFoundError:
    print("You need to download the folder 'py_common' from the community repo! (CommunityScrapers/tree/master/scrapers/py_common)", file=sys.stderr)
    sys.exit()

'''  This script runs a graphql function to bulk submit whatever scenes you pass in via Identify
     '''

def call_graphql(query, variables=None):
    return graphql.callGraphQL(query, variables)

def get_id(obj):
    ids = []
    for item in obj:
        ids.append(item['id'])
    return ids

def bulk_submit(scene):
    result = {}
    SubmittedTag = "4179"
    NeedsStashID = "4178"
    currenttags = get_id(scene["tags"])
    if SubmittedTag in currenttags:
      log.info("Scene already submitted")
      return result
    oktosubmit = True
    #if scene["stash_ids"] == []:
    if True:
      # check performers are all stashided
      for performer in scene["performers"]:
         if performer["stash_ids"] == []:
           oktosubmit = False
           log.info(performer["name"] + " needs a StashID")
           # tag performer to fix them
           tagging = {}
           tagging["id"] = performer["id"]
           tagging["tag_ids"] = get_id(performer["tags"])
           tagging["tag_ids"].append(NeedsStashID)
           query = """
            mutation tagforlater($input: PerformerUpdateInput!) {
                  performerUpdate(input: $input) { 
                   name 
                  }
            }
            """
           variables = {
             "input": tagging
           }
           log.debug(variables)
           result = call_graphql(query, variables)
           if result:
             log.info(result)

      if oktosubmit:
        submission = {}
        submission["id"] = scene["id"]
        submission["stash_box_index"] = 0
        query = """
            mutation BulkSubmitScene($input: StashBoxDraftSubmissionInput!) {
              submitStashBoxSceneDraft(input: $input)
            }
            """
        variables = {
          "input": submission
        }
        result = []
        result = call_graphql(query, variables)
        if result:
          log.info("Scene submitted as draft")
          log.info(result)
          tagging = {}
          tagging["id"] = scene["id"]
          tagging["tag_ids"] = currenttags
          tagging["tag_ids"].append(SubmittedTag)
          query = """
            mutation tagsubmitted($input: SceneUpdateInput!) {
                  sceneUpdate(input: $input) {
                   title
                  }
            }
            """
          variables = {
             "input": tagging
          }
          log.debug(variables)
          result = call_graphql(query, variables)
          if result:
             log.debug(result)

    else:
       log.info("already has Stash id, not resubmitted")
    return result

FRAGMENT = json.loads(sys.stdin.read())
SCENE_ID = FRAGMENT.get("id")
scene = graphql.getScene(SCENE_ID)
if scene["phash"]:
   bulk_submit(scene)
else:
   log.info("Scene lacks phash, so it was not submitted.  You should generate phashes for all scenes you wish to submit.")
print(json.dumps({}))
# Last Updated April 05, 2022
