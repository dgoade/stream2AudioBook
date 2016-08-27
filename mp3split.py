use strict;
use File::Find;
use File::Copy;
use IO::File;
use Time::Local;
use Getopt::Std;
use MP3::Info;
#use Log::Log4perl qw(:easy);
use Log::Log4perl;
use IO::CaptureOutput qw(capture capture_exec qxx);
#use Proc::Killall;
use Schedule::Cron;
use Time::Piece;
#use MP3::Tag;
#MP3::Tag->config(write_v24 => 1);
use MPEG::ID3v2Tag;

use IPC::Open3;
use IPC::Run3;
use IO::Handle;
use Capture::Tiny qw/capture/;

our $LameExe='C:/Program Files (x86)/Lame For Audacity/lame.exe';
our $Mp3SplitExe='C:/Program Files (x86)/mp3splt/mp3splt.exe';
our $MMConvertExe='C:/Program Files (x86)/MMConvert/1.0/MMConvert.exe';
our $ffmpegExe='C:/Program Files/ffmpeg-20130807-git-b45b1d7-win64-static/bin/ffmpeg.exe';
our $Kid3Exe='C:/Program Files (x86)/kid3/kid3-3.0.2-win32/kid3-cli.exe';

#C:\Users\sg0521891\Documents\downloads\NetTransport\Radio\raw

our $RawDir = 'C:/Users/David/Downloads/Radio';
our $EncodedDir = 'C:/Users/David/Downloads/Radio/recoded';
our $SplitDir = 'C:/Users/David/Dropbox';

our $DefaultRegex = "Radio-(\\w\\w)-(\\d\\d)(\\d\\d)-(\\d\\d)-(\\d\\d)\\.(mp3|asp|flv|wma)";
our $Regex=$DefaultRegex;
our $RemoveSourceAfter = 1;
our $Action="";
our $DryRun=0;
our %FileHash;
our ($opt_a, $opt_r, $opt_t, $opt_v, $opt_x);

&main;

sub init ()
{

	my $rval=1;
	my $logger;

	$logger = Log::Log4perl->get_logger('mp3split.init');

	#die;

	getopts('a:r:tv:x');

	# set action (what to do)
	if ( $opt_a )
	{
		$Action=$opt_a;
	}

	if ( $opt_r )
	{
		$Regex=$opt_r;
	}
	if ( $opt_x )
	{
		$RemoveSourceAfter=$opt_x;
	}

	if ( $opt_t )
	{
		$DryRun=1;
	}

	if ( -d $RawDir )
	{
		$logger->debug("Raw directory exists: $RawDir");
	}
	else
	{
		logger->error("Raw directory does not exist: $RawDir");
		$rval=0;
	}

	if ( -d $EncodedDir )
	{
		$logger->debug("Re-encoded directory exists: $EncodedDir");
	}
	else
	{
		logger->error("Re-encoded directory does not exist: $EncodedDir");
		$rval=0;
	}

	if ( -d $SplitDir )
	{
		$logger->debug("Split directory exists: $SplitDir");
	}
	else
	{
		logger->error("Split directory does not exist: $SplitDir");
		$rval=0;
	}

	return $rval;

}

sub runDaemonMode
{
	my $logger;
	my $cron;
	
	$logger = Log::Log4perl->get_logger('mp3split.runDaemonMode');
	
	# Create new object with default dispatcher
	$cron = new Schedule::Cron(\&runDaemonTasks);

	# Load a crontab file
	$cron->load_crontab("mp3split.cron");

	$logger->info("Begin runnning in daemon mode.");	
	#$cron->run(detach=>1,pid_file=>"/var/run/scheduler.pid");
	$cron->run();
	$logger->info("Scheduled jobs complete. Sleeping until next invocation.");


}

sub runDaemonTasks
{

	my $logger;
	my $date;
	
	my $mins;
	my $minTenth;
	
	$RemoveSourceAfter = 1;
	
	$logger = Log::Log4perl->get_logger('mp3split.runDaemonTasks');
	processRadioFiles($RawDir, $EncodedDir, $SplitDir, $RemoveSourceAfter);
}

sub main
{

	my $numSplitFiles=0;
	my $logger;

    Log::Log4perl::init_and_watch('log4perl.conf',10);

	$logger = Log::Log4perl->get_logger('mp3split.main');

	#$logger->debug('this is a debug message');
	#$logger->info('this is an info message');

	if ( &init() )
	{

		$logger->debug("Initialization successsful.");

		&globalVarDump();

		SWITCH: {
			$Action =~ /all/i && do 
				{
					processRadioFiles($RawDir, $EncodedDir, $SplitDir, $RemoveSourceAfter);
					last SWITCH;
				};

			$Action =~ /count/i && do 
				{
					$logger->info("Counting split files...");
					$numSplitFiles = &countFiles($Regex, $SplitDir);
					$logger->info("Split files=$numSplitFiles");
					last SWITCH;
				};

			$Action =~ /convert/i && do 
				{
					&prepMp3Files("convert", $RawDir, $EncodedDir);
					last SWITCH;
				};

			$Action =~ /daemon/i && do 
				{
					&runDaemonMode();
					last SWITCH;
				};

			$Action =~ /^(re)?encode/i && do 
				{
					&prepMp3Files("encode", $RawDir, $EncodedDir);
					last SWITCH;
				};

			$Action =~ /split/i && do 
				{
					&prepMp3Files("split", $EncodedDir, $SplitDir);
					last SWITCH;
				};

			$Action =~ /taglist/i && do 
				{
					&tagFilesID3v2($SplitDir, 0);
					last SWITCH;
				};
			$Action =~ /tag/i && do 
				{
					&tagFiles($SplitDir, 0);
					last SWITCH;
				};
			$Action =~ /test/i && do 
				{
					&runTest($SplitDir);
					last SWITCH;
				};

			DEFAULT: 
				$opt_v="debug";
				$logger->error("There is no action: $Action");
				&showUsage;
			};

	}
	else
	{
		$logger->fatal("Failed to initialize.");
	}

}

sub showUsage
{

	my $logger = Log::Log4perl->get_logger('mp3split.showUsage');

	$opt_v="debug";
	$logger->info("Usage: $0 [-a(ction) { all|count|encode|split|tag } ] [ -r(egexp) regexp ] [ -t(est) ]");
	$logger->info("You passed these options:");
	&optionDump;


}

sub optionDump
{

	my $logger = Log::Log4perl->get_logger('mp3split.optionDump');

	$logger->info("Option dump...");
	$logger->info("-a=$opt_a");
	$logger->info("-r=$opt_r");
	$logger->info("-t=$opt_t");
	$logger->info("-v=$opt_v");

}

sub globalVarDump
{

	my $logger = Log::Log4perl->get_logger('mp3split.globalVarDump');

	$logger->info("Global var dump...");
	$logger->info("\$Action=$Action");
	$logger->info("\$Regex=$Regex");
	$logger->info("\$DryRun=$DryRun");
	$logger->info("\$RemoveSourceAfter=$RemoveSourceAfter");
	
	$logger->info("\$LameExe=$LameExe");
	$logger->info("\$Mp3SplitExe=$Mp3SplitExe");
	$logger->info("\$ffmpegExe=$ffmpegExe");
	$logger->info("\$Kid2Exe=$Kid3Exe");
	$logger->info("\$RawDir=$RawDir");
	$logger->info("\$EncodedDir=$EncodedDir");
	$logger->info("\$SplitDir=$SplitDir");
	$logger->info("\$Regex=$Regex");

}

sub logIt
{

	if ( $opt_v )
	{
		print ("$_[0]");
	}

}

sub processRadioFiles()
{

	my $rval=1;
	my $rawDir = "$_[0]";
	my $encodedDir = "$_[1]";
	my $splitDir = "$_[2]";
	my $removeSourceAfter="$_[3]";
	
	my $thisFile;
	my $fileType;
	my $newFile;
	my $numSplitFiles;
	
	my $logger = Log::Log4perl->get_logger('mp3split.processRadioFiles');
	my @hashKeys;
	my $numKeys;
	my $logMsg;

	undef %FileHash;

	#$logger->debug("Dump of FileHash before executing the find...");
	for $thisFile (sort keys %FileHash)
	{	
		$logger->debug("$thisFile");
	}

	find(\&loadFileHash, $rawDir);
	
	@hashKeys = keys %FileHash;
	$numKeys = @hashKeys;
	
	if( $numKeys )
	{

		$logger->debug("Removing any non-radio files found.");
		for $thisFile (sort keys %FileHash)
		{	
			if( $thisFile =~ /(Radio)-(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)\.(asf|flv|wma|mp3)/ )
			{
				$logger->debug("Radio file found: $thisFile");
			}
			else
			{
				$logger->debug("Skipping non-radio file: $thisFile");
				delete($FileHash{$thisFile})					
			}
		}

		$logger->debug("Removing any files still open.");
		for $thisFile (sort keys %FileHash)
		{	
			if ( fileIsOpen($thisFile) )
			{
				$logger->warn("File is still open so skipping it: $thisFile");
				delete($FileHash{$thisFile})					
			}		
		}
			
		$logger->debug("Processing remaining radio files.");
		for $thisFile (sort keys %FileHash)
		{
			if( $thisFile =~ /^[^.]+\.(.*)$/ )
			{
				$fileType = $1;
				$logger->debug("Filetype is $fileType");
			}
			else
			{
				$logMsg = "Unable to parse file extension from this file so skipping it: $thisFile.";
				$logger->warn($logMsg);
				$rval = 0;
			}
			
			if( $rval ) 
			{
				if( $fileType =~ /asf|flv|wma/ )
				{
					$logger->debug("Attempting conversion of $thisFile");
					$newFile=convertFile($thisFile, $rawDir, 0);
					if( $newFile )
					{
						$logger->debug("Conversion successful.");
						if( $removeSourceAfter )
						{
							$logger->debug("Removing source file.");
							unlink $thisFile;								
						}
						else
						{
							$logMsg = "Not removing source file because removeSourceAfter is false.";
							$logger->debug($logMsg);
						}
						$thisFile = $newFile;
					}
					else
					{
						$logMsg = "Failed to convert the file -- leaving it for further investigation.";
						$logger->debug($logMsg);
						$rval = 0;
					}
				}
				elsif( $fileType =~ /mp3/ )
				{
					$logMsg = "File is already and mp3 file so no conversion necessary.";
				}					
			}
			
			if( $rval ) 
			{
				$logger->debug("Attempting encoding of $thisFile");
				$newFile=encodeFile($thisFile, $encodedDir);
				if( $newFile )
				{
					$logger->debug("Encoding successful.");
					if( $removeSourceAfter )
					{
						$logger->debug("Removing source file.");
						unlink $thisFile;
					}
					else
					{
						$logMsg = "Not removing source file because removeSourceAfter is false.";
						$logger->debug($logMsg);
					}
					$thisFile = $newFile;
				}
				else
				{
					$logMsg = "Failed to encode the file -- leaving it for further investigation.";
					$logger->debug($logMsg);
					$rval = 0;
				}
			}

			if( $rval ) 
			{
				$logger->debug("Attempting splitting of $thisFile");
				$numSplitFiles=splitFile($thisFile, $splitDir);
				if( $numSplitFiles )
				{
					$logger->debug("Successfully split $thisFile.");
					if( $removeSourceAfter )
					{
						$logger->debug("Removing source file.");
						unlink $thisFile;
					}
					else
					{
						$logMsg = "Not removing source file because removeSourceAfter is false.";
						$logger->debug($logMsg);
					}
				}
				else
				{
					$logMsg = "Failed to split the file -- leaving it for further investigation.";
					$logger->debug($logMsg);
					$rval = 0;
				}
			}
			
			if( $numSplitFiles )
			{		
				$logger->debug("Tagging files.");
				tagAllFiles($splitDir);
			}

		} # for $thisFile (sort keys %FileHash)
		
	}
	else
	{
		$logger->info("No files found to process.");
	} # if( $numKeys )

}

sub convertFile
{
 
	my $rval=1;

	my $exeName;

	my $objectFile = $_[0];
	my $objectFileFormat;
	my $outputDir=$_[1];
	my $checkIfOpen=$_[2];
	my $convertedFile;
	my $problems=0;

	my $prefix;
	my $artist;
	my $month;
	my $day;
	my $hour;
	my $minute;
	my $album;

	my $comm;

	my $logger;

	$logger = Log::Log4perl->get_logger('mp3split.convertFile');

	#Radio-JD-0228-16-30.mp3
	if ( $objectFile =~ /(Radio)-(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)\.(asf|flv|wma)/ )
	{

		$logger->info("File matches the convert regex: $objectFile");

		$prefix=$1;
		$artist=$2;
		$month=$3;
		$day=$4;
		$hour=$5;
		$minute=$6;
		$objectFileFormat=$7;
		$album="$artist $month / $day";

		if( $checkIfOpen )
		{
			if ( fileIsOpen($objectFile) )
			{
				$logger->warn("File is still open so skipping it: $objectFile");
				$rval=0;
			}
			else
			{
				$logger->info("File is not open so it should be safe to convert: $objectFile");
			}
		}
		else
		{
			$rval = 1;
		}
			
		if( $rval )
		{
			
			$convertedFile="$outputDir/$prefix-$artist-$month$day-$hour-$minute.mp3";
		
			if ( $objectFileFormat =~ /asf$/)
			{
				$convertedFile =~ s/\//\\/g;
				$logger->info("File is of asf type so using this converter: $MMConvertExe");
				$exeName="$MMConvertExe";
				$exeName =~ s/\//\\/g;
				$objectFile =~ s/\//\\/g;

				$comm="\"$exeName\" 
					if=\"$objectFile\" 
					of=\"$convertedFile\" 
					/f:mp3 |";

				$logger->debug("Converting file with the following command:");
				$logger->debug("$comm");

				if ( !$DryRun )
				{
					if ( open(STATUS, "$comm") )
						{ 
							if (<STATUS>)
							{
								$logger->debug("STATUS is true after opening command: $comm");
							}
							else
							{
								$logger->warn("STATUS is false after trying to open command: $comm");
							}
							while (<STATUS>)
							{
								$logger->debug("$_");
								if ( $_ =~ /skipping/ )
								{
									$problems=1;
								}
							}
						}
					else
						{
							$logger->fatal("FATAL! Command failed: \n $comm \n Due to error: $!");
							$rval=0;
						}
					close(STATUS);
				} # ( !$DryRun )
			}
			else
			{

				$logger->info("File is non-asf type so using this converter: $ffmpegExe");
		
				$exeName="$ffmpegExe";
				$exeName =~ s/\//\\/g;
				$objectFile =~ s/\//\\/g;

				$convertedFile="$outputDir/$prefix-$artist-$month$day-$hour-$minute.mp3";

				$comm="\"$exeName\" -y -i \"$objectFile\" \"$convertedFile\"";
				#ffmpeg -i input -acodec libfaac -ab 128k -vcodec mpeg4 -b 1200k -mbd 2 -flags +mv4+aic -trellis 2 -cmp 2 -subcmp 2 -s 320x180 -metadata title=X output.mp4

				$logger->debug("Converting file with the following command:");
				$logger->debug("$comm");

				`$comm`;
				# if ( open(STATUS, "$comm") )
				# { 
					# if (<STATUS>)
					# {
						# $logger->debug("STATUS is true after opening command: $comm");
					# }
					# else
					# {
						# $logger->warn("STATUS is false after trying to open command: $comm");
					# }
					# while (<STATUS>)
					# {
						# $logger->debug("$_");
						# #if ( $_ =~ /skipping/ )
						# #{
						# #	$problems=1;
						# #}
					# }
					# close(STATUS);
					
				# }
		
			}
			if ( $problems )
			{
				$logger->warn("Problems occurred during conversion.");
				$rval=0;
			}

		} # $rval 
	}
	else
	{
		$logger->info("File doesn't match the convert regex: $objectFile");
		$rval=0;
	}
	
	if( $rval )
	{
		$rval = $convertedFile;
	}
	else
	{
		undef $rval;
	}
	
	return $rval;

}

sub encodeFile
{
 
	my $rval=1;

	my $exeName="$LameExe";

	my $objectFile = $_[0];
	my $outputDir=$_[1];
	my $encodedFile;
	my $encodingProblems=0;

	my $prefix;
	my $artist;
	my $month;
	my $day;
	my $hour;
	my $minute;
	my $album;

	my $comm;

	my $logger;

	$logger = Log::Log4perl->get_logger('mp3split.encodeFile');

	#Radio-JD-0228-16-30.mp3
	if ( $objectFile =~ /(Radio)-(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)\.mp3/ )
	{
		$prefix=$1;
		$artist=$2;
		$month=$3;
		$day=$4;
		$hour=$5;
		$minute=$6;
		$album="$artist $month / $day";

		$encodedFile="$outputDir/$prefix-$artist-$month$day-$hour-$minute.mp3";
	
		$exeName =~ s/\//\\/g;
		$encodedFile =~ s/\//\\/g;
		$objectFile =~ s/\//\\/g;

		$comm="\"$exeName\" 
			--ta \"$artist\"
			--tl \"$album\"
			\"$objectFile\"
			\"$encodedFile\" |";

		$logger->debug("Encoding file with the following command:");
		$logger->debug("$comm");

		if ( !$DryRun)
		{
			if ( open(STATUS, "$comm") )
				{ 
					if (<STATUS>)
					{
						$logger->debug("STATUS is true after opening command: $comm");
					}
					else
					{
						$logger->warn("STATUS is false trying to open command: $comm");
					}
					while (<STATUS>)
					{
						$logger->debug("$_");
						if ( $_ =~ /skipping/ )
						{
							$encodingProblems=1;
						}
					}
				}
			else
				{
					$logger->fatal("FATAL! Command failed: \n $comm \n Due to error $!");
					$rval=0;
				}
			close(STATUS);

			if ( $encodingProblems )
			{
				$logger->warn("Problems occurred during encoding.");
				$rval=0;
			}
		}
	}
	else
	{
		$logger->debug("Non-mp3 file so not re-encoding with $LameExe.");
		$rval=0;
	}

	if( $rval )
	{
		$rval = $encodedFile;
	}
	else
	{
		undef $rval;
	}

	return $rval;

}


sub prepMp3Files()
{

	my $rval=1;
	my $action="$_[0]";
	my $inputDir="$_[1]";
	my $outputDir="$_[2]";
	my $removeSourceAfter="$_[3]";
	my $thisFile;
	my $logger = Log::Log4perl->get_logger('mp3split.prepMp3Files');
	my @hashKeys;
	my $numKeys;

	#&setDateRangeFromArg($date);

	undef %FileHash;

	#$logger->debug("Dump of FileHash before executing the find...");
	for $thisFile (sort keys %FileHash)
	{	
		$logger->debug("$thisFile");
	}

	find(\&loadFileHash, $inputDir);
	
	@hashKeys = keys %FileHash;
	$numKeys = @hashKeys;
	
	if( $numKeys )
	{

		for $thisFile (sort keys %FileHash)
		{       

			#if ( $rval )
			#{		

				SWITCH: {
					$action =~ /^convert/i && do 
						{

							$logger->debug("Attempting conversion: $thisFile");
							$rval=convertFile($thisFile, $outputDir);										
							last SWITCH;
						};

					$action =~ /^encode/i && do 
						{

							$logger->debug("Encoding: $thisFile");
							$rval=encodeFile($thisFile, $outputDir);
							last SWITCH;
						};

					$action =~ /^tryencode/i && do 
						{

							$logger->debug("Encoding using IO::CaptureOutput: $thisFile");
							$rval=tryEncodeFile($thisFile, $outputDir);
							last SWITCH;
						};

					$action =~ /split/i && do 
						{
							$logger->debug("Splitting: $thisFile");
							$rval=splitFile($thisFile, $outputDir);
							last SWITCH;
						};

					$action =~ /tag/i && do 
						{
							$logger->debug("Tagging: $thisFile");
							#if (!&splitFile($thisFile, $outputDir) )
							#{
							#	$rval=0;
							#}						
							last SWITCH;
						};

					DEFAULT: 
						$logger->debug("There is no action $action");
						$rval=0;
					};
					
					if( $rval && $removeSourceAfter )
					{
						$logger->debug("Removing source: $thisFile");
						unlink $thisFile;
					}
			#}
			#else
			#{
			#	$logger->error("Problems running $action on $thisFile.");
			#	$logger->error("Aborting processing on remaining files.");
			#	last;
			#}

		} # for $thisFile (sort keys %FileHash)
		
	}
	else
	{
		$logger->info("No files found to process.");
	}

}

sub loadFileHash
{

		my $dev;
		my $ino;
		my $mode;
		my $nlink;
		my $uid;
		my $gid;
		my $rdev;
		my $size;
		my $atime;
		my $mtime;
		my $ctime;
		my $blksize;
		my $blocks;
		my $filehandle;	
		my $regex;

		my $logger = Log::Log4perl->get_logger('mp3split.loadFileHash');

		if ( $Regex )
		{
			$regex="$Regex";
		}
		else
		{
			#Radio-JD-0228-16-30.mp3
			$regex=$DefaultRegex;
		}

		#print ("looking for $regex...\n");
		if ( $_ =~ /$regex/ )
		{
			#print "opening $_...\n";
			
			#my $filehandle = new IO::File;
			#$filehandle->open ($_) or die "Cannot open $_";


			#($dev, $ino, $mode, $nlink, $uid, $gid, $rdev, $size, $atime,
			#        $mtime, $ctime, $blksize, $blocks) = $filehandle->stat;

			#if ( $mtime >= $beginDateValue && $mtime <= $endDateValue )
			#{
					#print $File::Find::name . " - " . format_timestamp($mtime) . "\n";
					#print ("Found: $File::Find::name \n");
					$FileHash{$File::Find::name}="$mtime";

			#}

			#$filehandle->close;
		}


}

sub tagAllFiles
{
	my $inputDir=$_[0];
	my $thisFile;
	my $thisPrefix;
	my $lastPrefix;
	my $trackNum=0;
	my $logger = Log::Log4perl->get_logger('mp3split.tagAllFiles');

	$Regex=".*(Radio-\\w\\w-\\d\\d\\d\\d)-\\d\\d-\\d\\d-\\d\\d\\d\\.mp3\$";
	undef %FileHash;

	find(\&loadFileHash, $inputDir);

	for $thisFile (sort keys %FileHash)
	{       

		if ($thisFile =~ /$Regex/ )
		{
			$thisPrefix="$1";

			if ( $thisPrefix eq $lastPrefix )
			{
				$trackNum++;
			}
			else
			{
				$trackNum=1;
				$lastPrefix=$thisPrefix;
			}

			$logger->info("Tagging: $thisFile");

			&tagFile($thisFile, $trackNum);
		}
		else
		{
			$logger->warn("$thisFile doesn't match regex /(Radio-\w\w-\d\d\d\d)-\d\d-\d\d\.mp3/");
		}
	}

}

sub tagFilesID3v2
{
	my $inputDir=$_[0];
	my $retag=$_[1];
	my $thisFile;
	my $thisPrefix;
	my $lastPrefix;
	my $trackNum=0;
	my $logger = Log::Log4perl->get_logger('mp3split.tagFilesID3v2');

	#$Regex=".*(Radio-\\w\\w-\\d\\d\\d\\d)-\\d\\d-\\d\\d-\\d\\d\\d\\.mp3\$";
	undef %FileHash;

	find(\&loadFileHash, $inputDir);

	for $thisFile (sort keys %FileHash)
	{       
	
		if ($thisFile =~ /$Regex/ )
		{
			$thisPrefix="$1";

			if ( $thisPrefix eq $lastPrefix )
			{
				$trackNum++;
			}
			else
			{
				$trackNum=1;
				$lastPrefix=$thisPrefix;
			}

			$logger->info("Tagging: $thisFile");

			if( $retag )
			{
				&tagFileID3v2($thisFile, $trackNum);					
			}
			else
			{
				&listTagsID3v2($thisFile);
			}
		}
		else
		{
			$logger ->warn("$thisFile doesn't match regex /(Radio-\w\w-\d\d\d\d)-\d\d-\d\d\.mp3/");
		}
	}

}

sub listTagsID3v2
{
	my $rval=1;
	my $file=$_[0];
	my $logger;

	my $fh;
	my $tag;
	my $frame;
	
	my $kid3Exe="$Kid3Exe";
	my $com;
	my $pid;
    my $lineout;
    
	my $stderr;
    my $stdout;
	
	$logger = Log::Log4perl->get_logger('mp3split.listTagsID3v2');
	
	$kid3Exe =~ s/\//\\/g;
	$file  =~ s/\//\\/g;

	$com = '"' . $kid3Exe . '"' . " -c 'get' " . $file;
		
	$logger->debug("Getting tags with the following command:");
	$logger->debug("$com");
	
	#STDOUT->autoflush(1);
	#STDERR->autoflush(1);

	#my %options;
	#$options{"append_stdout"}=1;
	#$options{"append_stderr"}=1;
	#run3($com, undef, $stdout, $stderr, \%options);
		
	#print "$stdout\n";
	#print "$stderr\n";
	
	#$logger->debug($stdout);
	
	#open (STDERR,'>&$var'); print $var; 
	($stdout, $stderr) = capture {
		system ( "$com" );
		#system ( "zcho 'hello'" );
		#system ( "date" );
		#warn "Arg1!";
	};
	
	print "$stdout\n";
	print "$stderr\n";
	
	exit;

	if( <ERROR> )
	{
		while( $lineout = <ERROR> )
		{
			print "$lineout\n";
			#$logger->error("$lineout");
			#$rval=0;
			#if( $lineout =~ /^svnadmin: E.*/ )
			#{
				$rval=0;
			#	print "fail: $repo\n";
			#	if( $verboseOutput )
			#	{
			#		print "$lineout\n";
			#	}
			#	last;
			#}
		}
	}
	else
	{
		print "no errors\n";	
		while ( $lineout = <READER> )
		{
		   print "$lineout\n";
		   #$stdout.=$lineout;
		   #$logger->debug("$lineout");
		}
	}

	if( $rval )
	{
	}

	if( $rval )
	{
		$logger->debug("Command successful.");
	}

	if ( waitpid( $pid, 0 ) )
	{}
	else
	{
		$stderr .= "Unable to reap the command due to: $!";
		$rval=0;
    }


	#if ( open(STATUS, $com) )
	#{ 
	#	if (<STATUS>)
	#	{
	#		$logger->debug("STATUS is true after opening command: $com");
	#	}
	#	else
	#	{
	#		$logger->warn("STATUS is false trying to open command: $com");
	#	}
	#	while (<STATUS>)
	#	{
	#		$logger->debug("$_");
	#	}
	#}
	#else
	#{
	#	$logger->error("Command failed: \n $com \n Due to error $!");
	#	$rval=0;
	#}
	#close(STATUS);

	return $rval;
	
}

sub tagFileID3v2
{

	my $rval=1;
	my $file="$_[0]";
	my $trackNum="$_[1]";
	my $diskNum="";
	my $kid3Exe="$Kid3Exe";
	
	my $frame;
	my $name;
	my @info;
	my $info;
	my $key;
	my $val;
	
	my $prefix;
	my $artist;
	my $month;
	my $day;
	my $hour;
	my $minute;
	my $album;

	my $logger;

	$logger = Log::Log4perl->get_logger('mp3split.tagFileID3');
	
	$rval=listTagsID3v2($file);	

	if( $rval )
	{
		$logger->debug("Retagging ID3 tags for: $file");
	
		if ( $file =~ /.*(Radio-)(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)-(\d+)\.mp3$/ )
		{
			$prefix=$1;
			$artist=$2;
			$month=$3;
			$day=$4;
			$hour=$5;
			$minute=$6;
			$album="$artist $month / $day";
			$diskNum="";
		}
		
	}
	
	$rval=listTagsID3v2($file);

			# $logger->debug("Calling set_mp3tag($file, \"\", $artist, $album, \"\", \"\", \"\", $trackNum)");			

		# if (set_mp3tag ($file, "", $artist, $album, "", "", "", $trackNum))
		# {
			# $logger->debug("set_mp3tag call succeeded");
		# }
		# else
		# {
			# $logger->error("set_mp3tag call failed");
		# }
		

		# $tagInfoRef = get_mp3tag($file); #or die "No TAG info";
		# if ( $tagInfoRef )
		# {
			# $logger->debug("Now $file has tag info");
		# }
		# else
		# {
			# $logger->error("Failed to get tag info for $file after attempting to create it from file name.");
		# }
	# }

	#logIt ("Tag info for $file after changes:");
	# $logger->debug("Tag info for $file after changes:");
	# foreach my $thisKey (keys %{$tagInfoRef} )
	# {
	#	logIt ("$thisKey=$tagInfoRef->{$thisKey}\n");
		# $logger->debug("$thisKey=$tagInfoRef->{$thisKey}");
	# }

	return $rval;

}


sub tagFile
{

	my $file = "$_[0]";
	my $trackNum = "$_[1]";
    my $mp3 = new MP3::Info $file;

	my $tagInfoRef;
	my %tagInfo;

	my $prefix;
	my $artist;
	my $month;
	my $day;
	my $hour;
	my $minute;
	my $album;

	my $logger;

	$logger = Log::Log4perl->get_logger('mp3split.tagFile');

	$tagInfoRef = get_mp3tag($file); # or die "No TAG info";

	if ( $tagInfoRef )
	{
		#logIt ("Tag info for $file before changes:\n");
		$logger->debug("Tag info for $file before changes:");
		foreach my $thisKey (keys %{$tagInfoRef} )
		{
			#logIt ("$thisKey=$tagInfoRef->{$thisKey}\n");
			$logger->debug("$thisKey=$tagInfoRef->{$thisKey}");
		}

        $tagInfoRef->{TRACKNUM} = $trackNum;
        set_mp3tag($file, $tagInfoRef);

	}

	$logger->info("Retagging info for $file -- using filename.");
	
    if ( $file =~ /.*(Radio-)(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)-(\d+)\.mp3$/ )
	{
		$prefix=$1;
		$artist=$2;
		$month=$3;
		$day=$4;
		$hour=$5;
		$minute=$6;
		$album="$artist $month / $day";

		$logger->debug("Calling set_mp3tag($file, \"\", $artist, $album, \"\", \"\", \"\", $trackNum)");			

		if (set_mp3tag ($file, "", $artist, $album, "", "", "", $trackNum))
		{
			$logger->debug("set_mp3tag call succeeded");
		}
		else
		{
			$logger->error("set_mp3tag call failed");
		}
		

		$tagInfoRef = get_mp3tag($file); #or die "No TAG info";
		if ( $tagInfoRef )
		{
			$logger->debug("Now $file has tag info");
		}
		else
		{
			$logger->error("Failed to get tag info for $file after attempting to create it from file name.");
		}
	}

	#logIt ("Tag info for $file after changes:");
	$logger->debug("Tag info for $file after changes:");
	foreach my $thisKey (keys %{$tagInfoRef} )
	{
		#logIt ("$thisKey=$tagInfoRef->{$thisKey}\n");
		$logger->debug("$thisKey=$tagInfoRef->{$thisKey}");
	}


}


sub runTest
{

	my $exeName="$LameExe";
	my $found=0;
	my $logger;

	$logger = Log::Log4perl->get_logger('mp3split.runTest');
 
	$logger->debug("Executing $exeName");
	#open(NET, "dir |") or die "can't fork: $!";
	open(NET, "$exeName |") or die "can't fork: $!";
	while (<NET>) 
	{
		if ( $_ =~ /mp3split/ )
		{
			$found=1;
		}
		$logger->info("$_");
	}
	close(NET) or die "cant close: $!/$?";


	if ( $found )
	{
		print "found in the stdout";
		$logger->debug("found in the stdout");
	}
	else
	{
			$logger->debug("didn't find in the stdout");
	}

}

{ # Lexical scope of $numFile and $regex Globals

	my $numFiles=0;
	my $regex;

	sub countFiles
	{

		my $rval=1;
		my $dir=$_[1];
		my $logger = Log::Log4perl->get_logger('mp3split.countFiles');

		$regex=$_[0];

		find(\&filesMatching, $dir);				  
		$logger->debug("$numFiles files match this regex: $regex");

		return $numFiles;

	}

	sub filesMatching
	{

	    	if ( $_ =~ /$regex/ )
			{
				$numFiles++;
			}

	}

} # End of lexical scope of $numFile and $regex Globals

sub splitFile
{
 
        my $rval=1;

		my $exeName="$Mp3SplitExe";

		my $objectFile = $_[0];
		my $outputDir=$_[1];
		my $encodedFile;

		my $prefix;
		my $artist;
		my $month;
		my $day;
		my $hour;
		my $minute;
		my $album;
		my $startingTrack;

		my $comm;

		my $logger = Log::Log4perl->get_logger('mp3split.splitFile');
		#Radio-JD-0228-16-30.mp3
        if ( $objectFile =~ /(Radio)-(\w\w)-(\d\d)(\d\d)-(\d\d)-(\d\d)\.mp3/ )
		{
			$prefix=$1;
			$artist=$2;
			$month=$3;
			$day=$4;
			$hour=$5;
			$minute=$6;
			$album="$artist $month / $day";

			$encodedFile="$outputDir/$prefix-$artist-$month$day-$hour-$minute.mp3";
		}
		
		$exeName =~ s/\//\\/g;
		$encodedFile =~ s/\//\\/g;
		$outputDir =~ s/\//\\/g;
		$objectFile =~ s/\//\\/g;

		$comm="\"$exeName\" 
        	\"$objectFile\" 
        	-d \"$outputDir\" 
        	0.0.0 
        	-t 1.0 
        	-o $prefix-$artist-$month$day-$hour-$minute-\@n3|";

		$logger->debug("Splitting file with the following command:\n");
		$logger->debug("$comm\n");

		if ( !$DryRun)
		{
	        if (! (open STATUS, "$comm") )
	        	{ 
	        		$logger->fatal("FATAL! Command failed: \n $comm \n Due to error $!\n");
					$rval=0;
				}
	        close STATUS;
		}

        return $rval;

}

sub fileIsOpen
{

		my $rval=0;
		my $file=$_[0];

        my $dev;
        my $ino;
        my $mode;
        my $nlink;
        my $uid;
        my $gid;
        my $rdev;
        my $size1;
        my $size2;
        my $atime;
        my $mtime;
        my $ctime;
        my $blksize;
        my $blocks;
        my $filehandle;

		my $logger;

		$logger = Log::Log4perl->get_logger('mp3split.fileIsOpen');

        my $filehandle = new IO::File;

		$logger->debug("Opening file to get stats: $file");

        if ( $filehandle->open ($file) )
		{

			$logger->debug("Successfully opened file: $file");

			$logger->debug("Getting info about file: $file");
	        ($dev, $ino, $mode, $nlink, $uid, $gid, $rdev, $size1, $atime,
	                $mtime, $ctime, $blksize, $blocks) = $filehandle->stat;

	        if ( $filehandle->close )
			{
				$logger->debug("Successfully closed file: $file");

				$logger->debug("Sleeping for 5 seconds to see if it grows...");
				sleep 5;
						
		        if ( $filehandle->open ($file) )
				{
					$logger->debug("Successfully opened file: $file");
					$logger->debug("Re-getting info about file: $file");

			        ($dev, $ino, $mode, $nlink, $uid, $gid, $rdev, $size2, $atime,
			                $mtime, $ctime, $blksize, $blocks) = $filehandle->stat;

			        if ( $size1 == $size2  )
					{
						$logger->debug("File is not growing: $file");
					}
					else
			        {
						$logger->debug("File is growing: $file");				
						$rval=1;
			        }

			        if ( $filehandle->close )
					{
						$logger->debug("Successfully closed file: $file");
					}
					else
					{
						$logger->warn("Failed to close file: $file");
					}

				}
			}
			else
			{
				$logger->warn("Failed to close file: $file");
			}

		}
		else
		{
			$logger->error("Failed to open file $file -- will treat it as already open");
			$rval=1;
		}

        $filehandle->close;

		return $rval;

}
