#! /bin/bash
# maketasks.sh nrtasksperbucket
# Takes a bunch of csv buckets, and generates a list of random
# numberofbuckets*nrtasksperbucket, with equal number of tasks taken
# from each bucket

echo "url,longitude,latitude,datetime,score,size"
for x in *.csv; do
  shuf "$x" | head -n $1
done |
  shuf |
  sed -e "s+^\([^,]*\),+http://commondatastorage.googleapis.com/skytruth-temp%2Fiuu%2F\1.kml,+g" -e "s+$+,1000+g"
