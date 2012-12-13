#! /bin/sh
#Require pysam,ghmm package, python2.7 or higher version
#Require bedtools and samtools
#6 required parameters
#$1: Input SAM file
#$2: Shortest matched segment length
#$3: Maximum mismatch number
#$4: Remove PCR duplicates or not
#$5: FDR to determine enriched cluster
#$6: Minimum reads number in a cluster
#$7: CLIP type (0:HITS-CLIP; 1:PAR-CLIP(4SU); 2:PAR-CLIP(6SG))
#$8: FDR to determine reliable mutations
#$9: OUTPUT



############Process SAM################################
#Get matched entries and make them into sorted bam and index
samtools view -Sb $1 > temp.bam 2>dump
samtools sort ${__tool_data_path__}temp.bam temp.sorted
samtools index ${__tool_data_path__}temp.sorted.bam
samtools view -H ${__tool_data_path__}temp.bam > temp.header



#############Filter BAM by customized parameters#########
#-i: input file
#-o: $9 file prefix, prefix.fileter.sam will be provided to user
#-m: Shortest matched segment length
#-n: Maximum number of mismatch
SAMFilter_rmdup.py -i ${__tool_data_path__}temp.sorted.bam -o temp -m $2 -n $3 -r $4
samtools reheader ${__tool_data_path__}temp.header ${__tool_data_path__}temp.filter.bam > temp.filter.rehead.bam # should be sorted
samtools index ${__tool_data_path__}temp.filter.rehead.bam

#############Clustering the mapped reads################
clusterEnrich.py -i ${__tool_data_path__}temp.filter.rehead.bam -f $5 -n $6 > temp.filter.cluster.bed


#############Looking for mutations #########################
findMutationV2.py -i ${__tool_data_path__}temp.filter.rehead.bam -o temp.filter.mutation.bed -p $7
mutationFilter_pvalue.py -a ${__tool_data_path__}temp.filter.rehead.bam -b ${__tool_data_path__}temp.filter.mutation.bed -o temp.filter.reliable -p $7 -f $8 -c ${__tool_data_path__}temp.filter.bam.coverage


##############Intersect cluster with mutations ###############

	if test "$7" = "0" #HITS-CLIP, 3 $9
		then
		#echo $8,"HITS"
			finalMerge.py ${__tool_data_path__}temp.filter.cluster.bed ${__tool_data_path__}temp.filter.reliable_deletion.bed > CrossLinking_Site.deletion.out.bed
			finalMerge.py ${__tool_data_path__}temp.filter.cluster.bed ${__tool_data_path__}temp.filter.reliable_insertion.bed > CrossLinking_Site.insertion.out.bed
			finalMerge.py ${__tool_data_path__}temp.filter.cluster.bed ${__tool_data_path__}temp.filter.reliable_substitution.bed > CrossLinking_Site.substitution.out.bed
	fi	

	if test "$7" != "0" #PAR-CLIP, 1 $9
		then
		#echo $8,"PAR"
			finalMerge.py ${__tool_data_path__}temp.filter.cluster.bed ${__tool_data_path__}temp.filter.reliable.bed > CrossLinking_Site.out.bed
	fi

mv ${__tool_data_path__}temp.filter.cluster.bed filtered.cluster.out.bed
mv ${__tool_data_path__}temp.filter.mutation.bed filtered.mutation.out.bed
zip temp ${__tool_data_path__}length_distribution.pdf ${__tool_data_path__}filter_statistics.pdf ${__tool_data_path__}*.out.bed
mv ${__tool_data_path__}temp.zip $9
