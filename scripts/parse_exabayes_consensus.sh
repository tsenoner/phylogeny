for f in ExaBayes_*; do
  if [[ $f == *Newick* ]]; then
    mv "$f" "${f#ExaBayes_ConsensusExtendedMajorityRuleNewick.}.newick"
  elif [[ $f == *Nexus* ]]; then
    mv "$f" "${f#ExaBayes_ConsensusExtendedMajorityRuleNexus.}.nexus"
  fi
done
