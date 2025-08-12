#!/usr/bin/env openstudio
#
# SOURCE: https://github.com/canmet-energy/btap/
# LIBS: https://github.com/NREL/OpenStudio/

#require("openstudio-workflow")
##require("gli")
require("openstudio")
#require("openstudio_measure_tester")

puts "IDF/OSM conversion tool"

require('fileutils')

# Get the name of the model.
# @author Phylroy A. Lopez
# @return [String] the name of the model.
def get_name(model)
  unless model.building.get.name.empty?
    return model.building.get.name.get.to_s
  else
    return ""
  end
end

# @author Phylroy A. Lopez
# Get the name of the model.
# @author Phylroy A. Lopez
# @return [String] the name of the model.
def set_name(model,name)
  unless model.building.empty?
    model.building.get.setName(name)
  end
end

# This method loads an Openstudio file into the model.
# @author Phylroy A. Lopez
# @param filepath [String] path to the OSM file.
# @param name [String] optional model name to be set to model.
# @return [OpenStudio::Model::Model] an OpenStudio model object.
def load_idf(filepath, name = "")
  #load file
  unless File.exist?(filepath)
    raise 'File does not exist: ' + filepath.to_s
  end
  #puts "loading file #{filepath}..."
  model_path = OpenStudio::Path.new(filepath.to_s)
  #Upgrade version if required.
  version_translator = OpenStudio::OSVersion::VersionTranslator.new
  model = OpenStudio::EnergyPlus::loadAndTranslateIdf(model_path)
  version_translator.errors.each {|error| puts "Error: #{error.logMessage}\n\n"}
  version_translator.warnings.each {|warning| puts "Warning: #{warning.logMessage}\n\n"}
  #If model did not load correctly.
  if model.empty?
    raise 'something went wrong'
  end
  model = model.get
  if name != ""
    set_name(model,name)
  end
  #puts "File #{filepath} loaded."
  return model
end

# This method loads an Openstudio file into the model.
# @author Phylroy A. Lopez
# @param filepath [String] path to the OSM file.
# @param name [String] optional model name to be set to model.
# @return [OpenStudio::Model::Model] an OpenStudio model object.
def load_osm(filepath, name = "")

  #load file
  unless File.exist?(filepath)
    raise 'File does not exist: ' + filepath.to_s
  end
  #puts "loading file #{filepath}..."
  model_path = OpenStudio::Path.new(filepath.to_s)
  #Upgrade version if required.
  version_translator = OpenStudio::OSVersion::VersionTranslator.new
  model = version_translator.loadModel(model_path)
  version_translator.errors.each {|error| puts "Error: #{error.logMessage}\n\n"}
  version_translator.warnings.each {|warning| puts "Warning: #{warning.logMessage}\n\n"}
  #If model did not load correctly.
  if model.empty?
    raise "could not load #{filepath}"
  end
  model = model.get
  if name != "" and not name.nil?
    set_name(model,name)
  end
  #puts "File #{filepath} loaded."

  return model
end

# This method will save the model to an osm file.
# @author Phylroy A. Lopez
# @param model
# @param filename The full path to save to.
# @return [OpenStudio::Model::Model] a copy of the OpenStudio model object.
def save_osm(model,filename)
  FileUtils.mkdir_p(File.dirname(filename))
  File.delete(filename) if File.exist?(filename)
  model.save(OpenStudio::Path.new(filename))
  #puts "File #{filename} saved."
end

# This method will translate to an E+ IDF format and save the model to an idf file.
# @author Phylroy A. Lopez
# @param model
# @param filename The full path to save to.
# @return [OpenStudio::Model::Model] a copy of the OpenStudio model object.
def save_idf(model,filename)
  OpenStudio::EnergyPlus::ForwardTranslator.new().translateModel(model).toIdfFile().save(OpenStudio::Path.new(filename),true)
end

# This method will recursively translate all IDFs in a folder to OSMs, and save them to the OSM_-No_Space_Types folder
# @author Brendan Coughlin
# @param filepath The directory that holds the IDFs - usually DOEArchetypes\Original
# @return nil
def convert_idf_to_osm(filepath)
  Find.find(filepath) { |file|
    if file[-4..-1] == ".idf"
      model = load_idf(file)
      # this is a bit ugly but it works properly when called on a recursive folder structure
      #save_osm(model, (File.expand_path("..\\OSM-No_Space_Types\\", filepath) << "\\" << Pathname.new(file).basename.to_s)[0..-5])
      #save_osm(model, (Pathname.new(file).basename.to_s)[0..-5])
      filename= File.join( File.dirname(filepath), Pathname.new(file).basename.to_s[0..-5])
      save_osm(model, filename)
      myfile=File.join( File.dirname(filepath), "temp.osm" )
      File.open(myfile, 'w') { |file| file.write(model) }
    else
      puts "NOT an IDF file"
    end
  }
end

def convert_osm_to_idf(filepath)
  Find.find(filepath) { |file|
    if file[-4..-1] == ".osm"
      model = load_osm(file)
      # this is a bit ugly but it works properly when called on a recursive folder structure
      #save_osm(model, (File.expand_path("..\\OSM-No_Space_Types\\", filepath) << "\\" << Pathname.new(file).basename.to_s)[0..-5])
      #save_idf(model, (File.expand_path("..\\OSM-No_Space_Types\\", filepath) << "\\" << Pathname.new(file).basename.to_s)[0..-5])
      #save_idf(model, (Pathname.new(file).basename.to_s)[0..-5])
      filename= File.join( File.dirname(filepath), Pathname.new(file).basename.to_s[0..-5])
      save_idf(model, filename)
      #puts # empty line break
    else
      puts "NOT an OSM file"
    end
  }
end

if ARGV.length != 2
  puts "Two arguments required: --to-osm FILENAME.idf OR --to-idf FILENAME.osm"
  exit
end

if ARGV[0] =="--to-osm"
    convert_idf_to_osm(ARGV[1])
elsif ARGV[0] =="--to-idf"
    convert_osm_to_idf(ARGV[1])
else
    puts "invalid CLI option: --to-osm OR --to-idf"
end

puts "...DONE"
