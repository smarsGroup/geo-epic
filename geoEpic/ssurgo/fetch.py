

q = '''
SELECT DISTINCT 39.0321 as lat, -76.8740 as lon,lg.lkey,mu.mukey,co.cokey,ch.chkey,ctg.chtgkey,areaacres, projectscale,mu.musym, mu.muname, mukind, muacres, farmlndcl, iacornsr,
comppct_l, comppct_r, comppct_h, compname, compkind, majcompflag, slope_l, slope_r, slope_h, slopelenusle_l, slopelenusle_r, slopelenusle_h,
runoff, erocl, hydricrating, hydricon, drainagecl, elev_l, elev_r, elev_h, geomdesc, map_l, map_r, map_h, ffd_l, ffd_r, ffd_h, frostact,
hydgrp, taxclname, taxorder, taxsuborder, taxgrtgroup, taxsubgrp, taxpartsize, taxpartsizemod, taxceactcl, taxreaction, taxtempcl,
taxmoistscl, taxtempregime, soiltaxedition
,
hzname, desgndisc, desgnmaster, desgnmasterprime, desgnvert, hzdept_l, hzdept_r, hzdept_h, hzdepb_l, hzdepb_r, hzdepb_h, hzthk_l, hzthk_r,
hzthk_h, fraggt10_l, fraggt10_r, fraggt10_h, frag3to10_l, frag3to10_r, frag3to10_h, sieveno4_l, sieveno4_r, sieveno4_h, sieveno10_l,
sieveno10_r, sieveno10_h, sieveno40_l, sieveno40_r, sieveno40_h, sieveno200_l, sieveno200_r, sieveno200_h, sandtotal_l, sandtotal_r,
sandtotal_h, sandvc_l, sandvc_r, sandvc_h, sandco_l, sandco_r, sandco_h, sandmed_l, sandmed_r, sandmed_h, sandfine_l, sandfine_r,
sandfine_h, sandvf_l, sandvf_r, sandvf_h, silttotal_l, silttotal_r, silttotal_h, siltco_l, siltco_r, siltco_h, siltfine_l, siltfine_r,
siltfine_h, claytotal_l, claytotal_r, claytotal_h, claysizedcarb_l, claysizedcarb_r, claysizedcarb_h, om_l, om_r, om_h, dbtenthbar_r,
dbtenthbar_h, dbthirdbar_l, dbthirdbar_r, dbthirdbar_h, dbfifteenbar_l, dbfifteenbar_r, dbfifteenbar_h, dbovendry_l, dbovendry_r,
dbovendry_h, partdensity, ksat_l, ksat_r, ksat_h, awc_l, awc_r, awc_h, wtenthbar_l, wtenthbar_r, wtenthbar_h, wthirdbar_l, wthirdbar_r,
wthirdbar_h, wfifteenbar_l, wfifteenbar_r, wfifteenbar_h, wsatiated_l, wsatiated_r, wsatiated_h, ll_l, ll_r, ll_h, pi_l, pi_r, pi_h, kwfact,
kffact, caco3_l, caco3_r, caco3_h, gypsum_l, gypsum_r, gypsum_h, sar_l, sar_r, sar_h, ec_l, ec_r, ec_h, cec7_l, cec7_r, cec7_h, ecec_l,
ecec_r, ecec_h, sumbases_l, sumbases_r, sumbases_h, ph1to1h2o_l, ph1to1h2o_r, ph1to1h2o_h, ph01mcacl2_l, ph01mcacl2_r, ph01mcacl2_h,
pbray1_l, pbray1_r, pbray1_h, poxalate_l, poxalate_r, poxalate_h, ph2osoluble_l, ph2osoluble_r, ph2osoluble_h, ptotal_l, ptotal_r, ptotal_h
,texture, stratextsflag, ctg.rvindicator, texdesc, texcl,pmgroupname, pmg.rvindicator,reskind, resdept_l, resdept_r, resdept_h, resdepb_l, resdepb_r, resdepb_h, resthk_l, resthk_r, resthk_h
FROM sacatalog sc
LEFT JOIN legend lg ON sc.areasymbol = lg.areasymbol
LEFT JOIN (
SELECT * FROM mapunit
WHERE mukey in ('2455277')
) mu ON lg.lkey = mu.lkey
LEFT JOIN component co ON mu.mukey = co.mukey
LEFT JOIN chorizon ch ON co.cokey = ch.cokey
LEFT JOIN chtexturegrp ctg ON ch.chkey = ctg.chkey
LEFT JOIN chtexture ct ON ctg.chtgkey = ct.chtgkey
LEFT JOIN copmgrp pmg ON co.cokey = pmg.cokey
LEFT JOIN corestrictions rt ON co.cokey = rt.cokey
WHERE mu.mukey IS NOT NULL
AND compkind='Series' 
'''

import requests
import json
import pandas as pd

# Set the base URL and the specific endpoint for the POST request
base_url = "https://sdmdataaccess.nrcs.usda.gov"
endpoint = "/Tabular/SDMTabularService/post.rest"
full_url = base_url + endpoint

# Dictionary to hold the request parameters
request_params = {
    "format": "JSON+COLUMNNAME",
    "query": q  # Ensure 'q' is defined before this script runs
}

# Convert dictionary to JSON format for the POST request
request_data = json.dumps(request_params)

# Make the POST request to the server
response = requests.post(url=full_url, data=request_data)

# Parse the JSON response
response_data = response.json()

# Extract the column names and the data
columns = response_data.get('Table')[0]
data = response_data.get('Table')[1:]

# Create a DataFrame using the extracted data
property_result = pd.DataFrame(data, columns=columns)

# Print the resulting DataFrame
print(property_result)
