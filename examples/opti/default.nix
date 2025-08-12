with import <nixpkgs> {};
# SB- OS/Modelkit is here but not quite ready for release

let
  energyplus_file = "EnergyPlus-9.6.0-f420c06a69-Linux-Ubuntu20.04-x86_64.sh";
  openstudio_dir = "OpenStudio-3.3.0+ad235ff36e-Ubuntu-20.04";
  modelkit_file = "Modelkit_Catalyst_0.5.0_modelkit0.8.1.tar.xz";
  oldpkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-20.09.tar.gz") {};
  pkgs = import <nixpkgs> {};
  eplus_src = fetchurl {
    url = "https://github.com/NREL/EnergyPlus/releases/download/v9.6.0/EnergyPlus-9.6.0-f420c06a69-Linux-Ubuntu20.04-x86_64.sh";
    sha256 = "7b778259f9bb0b720289e4402fdbb35b85188324bff90c7a37e940543d7bbeb1";
  };
  os_src = fetchTarball {
    url = "https://github.com/NREL/OpenStudio/releases/download/v3.3.0/OpenStudio-3.3.0+ad235ff36e-Ubuntu-20.04.tar.gz";
    sha256 = "1bbc1yzvlx8l90z5mmkvdbwcy7ka6r0ypmmc8aqply3g25zz30qq";
  };
  gn_src = fetchTarball {
    url = "http://138.197.129.131/genEPJ_pkg.tar.gz";
    sha256 = "1p1ja2p2xrcjhxvyradbb5f2brmzbpa18s6a46f1q6wdwz71rja9";
  };
  di_src = fetchTarball {
    url = "http://138.197.129.131/genEPJ_support.tar.gz";
    sha256 = "11y2j9lcifn39nc208s20drhn82hda2hs0k03b6yw4p5hjv9m9d6";
  };
  eplus_epw = fetchTarball {
    url = "http://138.197.129.131/Ottawa_EPWs.tar.gz";
  };
  #mk_src = fetchTarball {
  #  url = "http://138.197.129.131/Modelkit_Catalyst_0.5.0_modelkit0.8.1.tar.xz";
  #  sha256 = "1l841qfjb6838jr460bnzhgpplca6ksdzx33rld7bv28hdwp3xjh";
  #};
in
pkgs.stdenv.mkDerivation rec {
  name = "genEPJ-full2024";

  src = ./.;

  buildInputs = [
    pkgs.python3 # done by requirements.txt
    pkgs.python311Packages.pip
    pkgs.python311Packages.numpy
    pkgs.python311Packages.pandas
    pkgs.python311Packages.matplotlib
    pkgs.python311Packages.scipy
    pkgs.python311Packages.virtualenv

    pkgs.bash
    pkgs.links2
    pkgs.nano
    pkgs.sqlite
    #pkgs.firefox
    #pkgs.jupyter
    pkgs.git
    pkgs.which
    #oldpkgs.ruby_2_7
    oldpkgs.ruby_2_6
    oldpkgs.rubyPackages_2_6.rake
    pkgs.dos2unix
  ];

  phases = [ "unpackPhase" "installPhase" ];

  unpackPhase = ''
    echo "Unpack Phase";
  '';


  installPhase = ''
    echo "Install Phase";

    # OS: Copying files and testing fetchTarball
    #mkdir -p $out/openstudio;
    #echo "${os_src}";
    #cp -r ${os_src}/usr/local/openstudio-*/* $out/openstudio/;

    # MK: Copying files and testing fetchTarball
    mkdir -p $out/modelkit;

    ## TODO- get from ubuntu server instead (WORKS)
    ##echo "{mk_src}";
    #cp -r "${src}/temp/gem" "$out/modelkit/gem";
    #export GEM_PATH=${oldpkgs.ruby_2_6}/lib/ruby/gems/2.6.0/:$out/modelkit/gem/ruby/2.6.0;
    #export GEM_HOME=$GEM_PATH;

    #DOESNT WORK. Keep as history of trials
    #${oldpkgs.ruby_2_6}/bin/gem install --local {mk_src}/lib/rubygems/gems/modelkit-0.8.1/modelkit-0.8.1.gem --install-dir=$out/modelkit --ignore-dependencies;
    #mkdir -p $out/modelkit/gem;
    #cp -r ${oldpkgs.ruby_2_6}/lib/ruby/gems/2.6.0/* $out/modelkit/gem/;
    #echo "${oldpkgs.rubyPackages_2_6.rake}";
    #cp -r {mk_src}/* $out/modelkit/;
    #${oldpkgs.ruby_2_6}/bin/gem install --local $out/modelkit/lib/rubygems/gems/modelkit-0.8.1/modelkit-0.8.1.gem --install-dir=$out/modelkit/gem/ --ignore-dependencies;
    #${oldpkgs.ruby_2_6}/bin/gem install --local $out/modelkit/lib/rubygems/gems/modelkit-0.8.1/modelkit-0.8.1.gem --install-dir=${oldpkgs.ruby_2_6}/lib/ruby/gems/2.6.0 --ignore-dependencies;
    #export GEM_PATH=${oldpkgs.ruby_2_6}/lib/ruby/gems/2.6.0;
    #${oldpkgs.ruby_2_6}/bin/bundle update rake
    #cd $out/modelkit/lib/rubygems/gems/modelkit-0*/ && rake
    #cd $out/modelkit/lib/rubygems/gems/modelkit-0*/ && ${oldpkgs.rubyPackages_2_6.rake}/bin/rake
    #${oldpkgs.ruby_2_6}/bin/gem install rake --install-dir=$out/modelkit/gem;
    #${oldpkgs.ruby_2_6}/bin/gem install --local result/modelkit/lib/rubygems/gems/modelkit-0.8.1/modelkit-0.8.1.gem --install-dir=result/modelkit/gem;
    #cd $out/modelkit/lib/rubygems/gems/modelkit-*/ && chmod +x bin/modelkit && dos2unix bin/modelkit && ${oldpkgs.rubyPackages_2_6.rake}/bin/rake && ${oldpkgs.ruby_2_6}/bin/gem install modelkit
    #cd $out/modelkit/lib/rubygems/gems/modelkit-0* && ${oldpkgs.ruby_2_6}/bin/gem install modelkit --install-dir=$out/modelkit/gem
    #cd $out/modelkit/lib/rubygems/gems/modelkit-0* && ${oldpkgs.ruby_2_6}/bin/gem install modelkit --install-dir=${oldpkgs.ruby_2_6}/lib/ruby/gems/2.6.0

    echo bash ${pkgs.bash};
    mkdir -p $out/etc/bash;
    mkdir -p $out/bin;
    cp ${pkgs.bash}/bin/bash $out/bin/bash;

    # genEPJ install
    echo "Source ${gn_src}"; # genEPJ source file
    cp -r "${gn_src}" "$out/genEPJ_pkg";
    cp -r "${di_src}" "$out/genEPJ_support";
    #Use makefile for python packages)
    echo """numpy-financial>=1.0.0 # cash_flow
platypus-opt>=1.0 # optimization
eppy>0.5 # OPTIONAL eppy template capabilities
""" > $out/requirements.txt
    echo """
init:
	virtualenv -p python3 venv
	./venv/bin/pip install -r $out/requirements.txt
	echo "source venv/bin/activate"
clean:
	rm -rf expandedidf* data_temp *opti.idf *sql *idd eplus* Energy+* in.* OptiHouse_errors.txt *_optiNPV.csv OptiHouse_results.txt GenOpt.log OutputListingAll.txt OutputListingMain.txt Output tmp-genopt* opt_soln *epw basement_regression_equation.m *pyc sim_errors.txt modelkit_cmd.sh LOGS_Modelkit.txt
	rm -rf raw_resil.csv __pycache__ 01_post_outage_resil?.csv 02_diff_outage.csv result3RV_resil?.txt resultVoLL_resil?.csv 00_pre_outage_resil?.csv expandedidf.err resultVoLL*.csv *blended* LOG_run_multiple_location_resilience.txt
""" > $out/makefile

    # Install EnergyPlus
    mkdir -p $out/energyplus
    cp "${eplus_src}" "$out/energyplus/${energyplus_file}";

    chmod +x "$out/energyplus/${energyplus_file}";
    sed -i 's/read line leftover/line="yes"; cpack_license_accepted=TRUE;/g' "$out/energyplus/${energyplus_file}";
    sed -i 's/link_directory=""/link_directory="n"/g' "$out/energyplus/${energyplus_file}";
    sed -i 's/read link_directory/echo "link directory ignored"/g' "$out/energyplus/${energyplus_file}";
    sed -i 's/install_dir_ok=0/install_dir_ok=1/g' "$out/energyplus/${energyplus_file}";
    sed -i 's|install_directory=""|install_directory="."|g' "$out/energyplus/${energyplus_file}";
    cd "$out/energyplus/" && bash "./${energyplus_file}";

    # EPW install for Ottawa (and outage events)
    cp -r "${eplus_epw}" "$out/energyplus/WeatherData/EPWs";

#    ## ModelKit setup
#    mkdir -p $out/modelkit;
#    cp "$src/temp/${modelkit_file}" "$out/modelkit/";
#    cd "$out/modelkit/" &&  unzip "${modelkit_file}" && echo "More to come";
#
#    # OpenStudio setup
#    mkdir -p $out/openstudio;
#    cp "$src/temp/${openstudio_dir}.zip" "$out/openstudio/";
#    cd "$out/openstudio/" &&  unzip "${openstudio_dir}.zip" && echo "More to come";
#
#    echo modelkit ruby ${oldpkgs.ruby_2_6};
#    echo openstudio ruby ${oldpkgs.ruby_2_7};

    # Add basic exports to bashrc
    echo 'export LC_ALL="en_US.utf8"' > $out/etc/bash/bashrc;
    #echo "export GEM_PATH=${oldpkgs.ruby_2_6}/lib/ruby/gems/2.6.0/:$out/modelkit/gem/ruby/2.6.0" >> $out/etc/bash/bashrc;
    #echo "export GEM_HOME=$GEM_PATH" >> $out/etc/bash/bashrc;
    #echo "alias ruby2.6=\"${oldpkgs.ruby_2_6}/bin/ruby\"" >> $out/etc/bash/bashrc;
    #echo "alias rake2.6=\"${oldpkgs.ruby_2_6}/bin/rake\"" >> $out/etc/bash/bashrc;
    #echo "alias gem2.6=\"${oldpkgs.ruby_2_6}/bin/gem\"" >> $out/etc/bash/bashrc;
    #echo "alias ruby2.7=\"${oldpkgs.ruby_2_7}/bin/ruby\"" >> $out/etc/bash/bashrc;
    #echo "alias rake2.7=\"${oldpkgs.ruby_2_7}/bin/rake\"" >> $out/etc/bash/bashrc;
    #echo "alias gem2.7=\"${oldpkgs.ruby_2_7}/bin/gem\"" >> $out/etc/bash/bashrc;
    echo "export ENERGYPLUS_DIR=$out/energyplus" >> $out/etc/bash/bashrc;
    echo 'export ENERGYPLUS_WEATHER=$ENERGYPLUS_DIR/WeatherData/EPWs' >> $out/etc/bash/bashrc;
    #echo 'export ENERGYPLUS_DIR=result/energyplus' >> $out/etc/bash/bashrc;
    #echo "export ENERGYPLUS_WEATHER=$src/EPWs/" >> $out/etc/bash/bashrc;

    #echo "export PATH=$PATH:result/energyplus/:result/openstudio/${openstudio_dir}/usr/local/openstudio-3.3.0/bin:$out/modelkit/gem/ruby/2.6.0/bin:${pkgs.python311Packages.pip}/bin:${pkgs.python311Packages.virtualenv}/bin" >> $out/etc/bash/bashrc;
    echo "export PATH=$PATH:$out/energyplus/:${pkgs.python311Packages.pip}/bin:${pkgs.python311Packages.virtualenv}/bin" >> $out/etc/bash/bashrc;
  '';

  # Launch into bash after building
  shellHook = ''
    echo "Launching into Bash shell...";
    source result/etc/bash/bashrc;
    source $src/venv/bin/activate;
    echo "Install python libraries to venv using: 'make -f result/makefile init' Then 'source venv/bin/activate'";
    exec $SHELL
  '';

  meta = {
    description = "Custom genEPJ environment with Python 3, Firefox, Jupyter Notebook, and Bash";
    homepage = "https://example.com";
    #license = licenses.mit;
  };
}
