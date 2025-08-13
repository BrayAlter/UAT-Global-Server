<template>
  <div id="create-task-list-modal" class="modal fade" data-backdrop="static" data-keyboard="false">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content" :class="{ 'dimmed': showAoharuConfigModal || showSupportCardSelectModal }">
        <div class="modal-header d-flex align-items-center justify-content-between">
          <h5 class="mb-0">Create New Task</h5>
          <div class="header-actions">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="cancelTask">Cancel</button>
            <button type="button" class="btn btn-sm btn-primary" @click="addTask">Confirm</button>
          </div>
        </div>
        <div class="modal-body modal-body--split" ref="scrollPane">
          <div class="side-nav">
            <div class="side-nav-title">Sections</div>
            <ul class="side-nav-list">
              <li v-for="s in sectionList" :key="s.id">
                <a href="#" :class="{ active: activeSection === s.id }" @click.prevent="scrollToSection(s.id)">{{ s.label }}</a>
              </li>
            </ul>
          </div>
          <form class="content-pane">
            <div class="category-card" id="category-general">
              <div class="category-title">General</div>
            <div class="form-group">
              <label for="selectTaskType">⭐ Task Selection</label>
              <select v-model="selectedUmamusumeTaskType" class="form-control" id="selectTaskType">
                <option v-for="task in umamusumeTaskTypeList" :value="task">{{ task.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="selectExecuteMode">⭐ Execution Mode</label>
              <select v-model="selectedExecuteMode" class="form-control" id="selectExecuteMode">
                <option value=1>One-time</option>
              </select>
            </div>
            <div class="row">
              <div class="col">
                <div class="form-group">
                  <label for="selectScenario">⭐ Scenario Selection</label>
                  <select v-model="selectedScenario" class="form-control" id="selectScenario">
                    <option :value="1">URA</option>
                    <option :value="2">Aoharu Cup</option>
                  </select>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="selectUmamusume">Uma Musume Selection</label>
                  <select disabled class="form-control" id="selectUmamusume">
                    <option value=1>Use Last Selection</option>
                  </select>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="selectAutoRecoverTP">Auto-recover when TP is low (TP Bottle)</label>
                  <select v-model="recoverTP" class="form-control" id="selectAutoRecoverTP">
                    <option :value=true>Yes</option>
                    <option :value=false>No</option>
                  </select>
                </div>
              </div>
            </div>
            <!-- URA Additional Configuration -->
            <div class="row" v-if="selectedScenario === 1">
              <div class="col-4">
                <div class="form-group">
                  <span class="btn auto-btn ura-btn-bg" style="width: 100%; background-color:#6c757d;"
                    v-on:click="openUraConfigModal">URA Configuration</span>
                </div>
              </div>
            </div>
            <!-- Youth Cup Additional Configuration -->
            <div class="row" v-if="selectedScenario === 2">
              <div class="col-4">
                <div class="form-group">
                  <span class="btn auto-btn aoharu-btn-bg" style="width: 100%; background-color:#6c757d;"
                    v-on:click="openAoharuConfigModal">Aoharu Cup Configuration</span>
                </div>
              </div>
            </div>
            </div>
            <!-- Limited Time Module: Fujikiseki Show Mode -->
            <!-- <div class="row">
              <div class="col-3">
                <div class="form-group">
                  <label>⏰ Fujikiseki Show Mode</label>
                  <select v-model="fujikisekiShowMode" class="form-control">
                    <option :value=true>Yes</option>
                    <option :value=false>No</option>
                  </select>
                </div>
              </div>
              <div class="col-2">
                <div class="form-group">
                  <label :style="{ color: fujikisekiShowMode ? '' : 'lightgrey' }">Select Difficulty</label>
                  <select v-model="fujikisekiShowDifficulty" class="form-control" :disabled="!fujikisekiShowMode">
                    <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
                  </select>
                </div>
              </div>
            </div> -->
            <div class="category-card" id="category-preset">
              <div class="category-title">Preset &amp; Support Card</div>
            <div class="row">
              <div class="col-8">
                <div class="form-group">
                  <label for="race-select">⭐ Use Preset</label>
                  <div class="input-group input-group-sm">
                    <select v-model="presetsUse" class="form-control" id="use_presets">
                      <option v-for="set in cultivatePresets" :value="set">{{ set.name }}</option>
                    </select>
                    <div class="input-group-append">
                      <button type="button" class="btn btn-sm auto-btn" @click="applyPresetRace">Apply</button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-4">
                <div class="form-group preset-actions">
                  <label>Save Preset</label>
                  <div class="dropdown preset-save-group">
                    <button type="button" class="btn btn-sm btn-outline-primary dropdown-toggle align-self-stretch" @click="togglePresetMenu">Save Preset</button>
                    <div class="dropdown-menu show" v-if="showPresetMenu">
                      <a href="#" class="dropdown-item" @click.prevent="selectPresetAction('add')">Add new preset</a>
                      <a href="#" class="dropdown-item" @click.prevent="selectPresetAction('overwrite')">Overwrite preset</a>
                      <a href="#" class="dropdown-item text-danger" @click.prevent="selectPresetAction('delete')">Delete saved preset</a>
                    </div>
                  </div>
                  <div v-if="presetAction==='add'" class="mt-1">
                    <div class="input-group input-group-sm">
                      <input v-model="presetNameEdit" type="text" class="form-control" placeholder="Preset Name">
                      <div class="input-group-append">
                        <button class="btn btn-sm auto-btn" type="button" @click="confirmAddPreset">Save</button>
                      </div>
                    </div>
                  </div>
                  <div v-if="presetAction==='overwrite'" class="mt-1">
                    <div class="input-group input-group-sm">
                      <select v-model="overwritePresetName" class="form-control">
                        <option v-for="set in cultivatePresets.filter(p=>p.name!=='Default')" :key="set.name" :value="set.name">{{ set.name }}</option>
                      </select>
                      <div class="input-group-append">
                        <button class="btn btn-sm auto-btn" type="button" @click="confirmOverwritePreset">Overwrite</button>
                      </div>
                    </div>
                  </div>
                  <div v-if="presetAction==='delete'" class="mt-1">
                    <div class="input-group input-group-sm">
                      <select v-model="deletePresetName" class="form-control">
                        <option v-for="set in cultivatePresets.filter(p=>p.name!=='Default')" :key="set.name" :value="set.name">{{ set.name }}</option>
                      </select>
                      <div class="input-group-append">
                        <button class="btn btn-danger btn-sm" type="button" @click="confirmDeletePreset">Delete</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="row">
              <div class="col-6">
                <div class="form-group">
                  <label>⭐ Friend Support Card Selection</label>
                  <div class="input-group input-group-sm">
                    <input type="text" class="form-control" :value="renderSupportCardText(selectedSupportCard)" readonly id="selectedSupportCard">
                    <div class="input-group-append">
                      <button type="button" class="btn btn-sm auto-btn" @click="openSupportCardSelectModal">Change</button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="col-3">
                <div class="form-group">
                  <label for="selectSupportCardLevel">Support Card Level (≥)</label>
                  <input v-model="supportCardLevel" type="number" class="form-control" id="selectSupportCardLevel"
                    placeholder="">
                </div>
              </div>
            </div>
            </div>
            <div class="category-card" id="category-career">
              <div class="category-title">Career Settings</div>
              <div class="row">
                <div class="col-3">
                  <div class="form-group">
                    <label for="inputClockUseLimit">Clock Usage Limit</label>
                    <input v-model="clockUseLimit" type="number" class="form-control" id="inputClockUseLimit" placeholder="">
                  </div>
                </div>
              </div>
              <div class="form-group">
                <div>⭐ Target Attributes (If unsure about specific values, manually train once and input the final stats)</div>
              </div>
            <div class="row">
              <div class="col">
                <div class="form-group">
                  <label for="speed-value-input">Speed</label>
                  <div class="input-group input-group-sm">
                    <input type="number" v-model="expectSpeedValue" class="form-control" id="speed-value-input">
                    <div class="input-group-append"><span class="input-group-text">pt</span></div>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="stamina-value-input">Stamina</label>
                  <div class="input-group input-group-sm">
                    <input type="number" v-model="expectStaminaValue" class="form-control" id="stamina-value-input">
                    <div class="input-group-append"><span class="input-group-text">pt</span></div>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="power-value-input">Power</label>
                  <div class="input-group input-group-sm">
                    <input type="number" v-model="expectPowerValue" class="form-control" id="power-value-input">
                    <div class="input-group-append"><span class="input-group-text">pt</span></div>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="will-value-input">Guts</label>
                  <div class="input-group input-group-sm">
                    <input type="number" v-model="expectWillValue" class="form-control" id="will-value-input">
                    <div class="input-group-append"><span class="input-group-text">pt</span></div>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="intelligence-value-input">Wit</label>
                  <div class="input-group input-group-sm">
                    <input type="number" v-model="expectIntelligenceValue" class="form-control" id="intelligence-value-input">
                    <div class="input-group-append"><span class="input-group-text">pt</span></div>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-group">
              <div>⭐ Desire Mood (Customize the desire Mood per year)</div>
            </div>
            <div class="row">
              <div class="col">
                <div class="form-group">
                  <label for="motivation-year1">Year 1</label>
                  <div class="input-group input-group-sm">
                    <select v-model="motivationThresholdYear1" class="form-control" id="motivation-year1">
                      <option :value=1>Awful</option>
                      <option :value=2>Bad</option>
                      <option :value=3>Normal</option>
                      <option :value=4>Good</option>
                      <option :value=5>Great</option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="motivation-year2">Year 2</label>
                  <div class="input-group input-group-sm">
                    <select v-model="motivationThresholdYear2" class="form-control" id="motivation-year2">
                      <option :value=1>Awful</option>
                      <option :value=2>Bad</option>
                      <option :value=3>Normal</option>
                      <option :value=4>Good</option>
                      <option :value=5>Great</option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="motivation-year3">Year 3</label>
                  <div class="input-group input-group-sm">
                    <select v-model="motivationThresholdYear3" class="form-control" id="motivation-year3">
                      <option :value=1>Awful</option>
                      <option :value=2>Bad</option>
                      <option :value=3>Normal</option>
                      <option :value=4>Good</option>
                      <option :value=5>Great</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col">
                <div class="form-group">
                  <div class="form-check">
                    <input type="checkbox" v-model="prioritizeRecreation" class="form-check-input" id="prioritizeRecreation">
                    <label class="form-check-label" for="prioritizeRecreation">
                      ⭐ Prioritize Recreation (Pal Type Support Card)
                    </label>
                  </div>
                  <small class="form-text text-muted">(optional) only use this if you bring Pal type Support Card like Tazuna in Career</small>
                </div>
              </div>
            </div>
            <div>
              <div class="form-group">
                <div class="advanced-options-header" @click="switchAdvanceOption">
                  <div class="advanced-options-title">
                    <i class="fas fa-cogs"></i>
                    Advanced Options
                  </div>
                  <div class="advanced-options-toggle">
                    <span class="toggle-text">{{ showAdvanceOption ? 'Hide' : 'Show' }}</span>
                    <i class="fas" :class="showAdvanceOption ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="showAdvanceOption" class="advanced-options-content">
              <div class="form-group">
                <div>⭐ Extra Weight</div>
              </div>
              <p>Adjusts AI training preferences without affecting final target attributes. Generally used to prioritize
                certain training types. Weight range [-1.0 ~ 1.0], 0 means no extra weight applied.</p>
              <p>❗ Setting weight to -1 will skip that training</p>
              <p>❗ Within the same year, all weights cannot be -1</p>
              <p>When support cards or uma legacy are weak, recommend increasing one attribute weight while
                decreasing others by the same amount</p>
              <div style="margin-bottom: 10px;">Year 1</div>
              <div class="row">
                <div v-for="v, i in extraWeight1" class="col">
                  <div class="form-group">
                    <input type="number" v-model="extraWeight1[i]" class="form-control"
                      @input="onExtraWeightInput(extraWeight1, i)" id="speed-value-input">
                  </div>
                </div>
              </div>
              <div style="margin-bottom: 10px;">Year 2</div>
              <div class="row">
                <div v-for="v, i in extraWeight2" class="col">
                  <div class="form-group">
                    <input type="number" v-model="extraWeight2[i]" class="form-control"
                      @input="onExtraWeightInput(extraWeight2, i)" id="speed-value-input">
                  </div>
                </div>
              </div>
              <div style="margin-bottom: 10px;">Year 3</div>
              <div class="row">
                <div v-for="v, i in extraWeight3" class="col">
                  <div class="form-group">
                    <input type="number" v-model="extraWeight3[i]" class="form-control"
                      @input="onExtraWeightInput(extraWeight3, i)" id="speed-value-input">
                  </div>
                </div>
              </div>
            </div>

            </div>
            <div class="category-card" id="category-race">
              <div class="category-title">Race Settings</div>
            <div class="form-group">
              <div>⭐ Racing Style Selection</div>
            </div>
            <div class="row">
              <div class="col">
                <div class="form-group">
                  <label for="selectTactic1">Year 1</label>
                  <div class="input-group input-group-sm">
                    <select v-model="selectedRaceTactic1" class="form-control" id="selectTactic1">
                      <option :value=1>End-Closer</option>
                      <option :value=2>Late-Surger</option>
                      <option :value=3>Pace-Chaser</option>
                      <option :value=4>Front-Runner</option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="selectTactic2">Year 2</label>
                  <div class="input-group input-group-sm">
                    <select v-model="selectedRaceTactic2" class="form-control" id="selectTactic2">
                      <option :value=1>End-Closer</option>
                      <option :value=2>Late-Surger</option>
                      <option :value=3>Pace-Chaser</option>
                      <option :value=4>Front-Runner</option>
                    </select>
                  </div>
                </div>
              </div>
              <div class="col">
                <div class="form-group">
                  <label for="selectTactic3">Year 3</label>
                  <div class="input-group input-group-sm">
                    <select v-model="selectedRaceTactic3" class="form-control" id="selectTactic3">
                      <option :value=1>End-Closer</option>
                      <option :value=2>Late-Surger</option>
                      <option :value=3>Pace-Chaser</option>
                      <option :value=4>Front-Runner</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <div class="form-group">
              <div class="row">
                <div class="col">
                  <div class="form-group">
                    <label for="race-select">⭐ Additional Race Schedule</label>
                    <textarea type="text" disabled v-model="extraRace" class="form-control" id="race-select"></textarea>
                  </div>
                </div>
              </div>
              <div class="form-group">
                <div class="race-options-header" @click="switchRaceList">
                  <div class="race-options-title">
                    <i class="fas fa-flag-checkered"></i>
                    Race Options
                  </div>
                  <div class="race-options-toggle">
                    <span class="toggle-text">{{ showRaceList ? 'Hide' : 'Show' }}</span>
                    <i class="fas" :class="showRaceList ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                  </div>
                </div>
              </div>
              <div v-if="showRaceList" class="race-options-content">
                <!-- Race Filter Controls (tidy grid) -->
                <div class="race-filters mb-3">
                  <div class="filter">
                    <label>🔍 Search Races:</label>
                    <input type="text" v-model="raceSearch" class="form-control" placeholder="Search by race name...">
                  </div>
                  <div class="filter">
                    <label>👤 Character Filter: <i class="fas fa-info-circle text-muted" title="Filter races based on character's terrain/distance aptitude and training schedule"></i></label>
                    <select v-model="selectedCharacter" class="form-control" @change="onCharacterChange">
                      <option value="">All Characters</option>
                      <option v-for="character in characterList" :key="character.name" :value="character.name">
                        {{ character.name }}</option>
                    </select>
                    <small v-if="selectedCharacter" class="text-info">
                      {{ getCompatibleRacesCount() }} compatible, {{ getIncompatibleRacesCount() }} filtered out
                    </small>
                    <small v-else class="text-muted">
                      Select a character to filter races by compatibility
                    </small>
                  </div>
                  <div class="quick">
                    <label>🏁 Quick Selection:</label>
                    <div class="btn-group" role="group">
                      <button type="button" class="btn btn-sm btn-outline-success" @click="selectAllGI">Select All GI</button>
                      <button type="button" class="btn btn-sm btn-outline-success" @click="selectAllGII">Select All GII</button>
                      <button type="button" class="btn btn-sm btn-outline-success" @click="selectAllGIII">Select All GIII</button>
                      <button type="button" class="btn btn-sm btn-outline-warning" @click="clearAllRaces">Clear All</button>
                    </div>
                  </div>

                  <div class="filter">
                    <label>🏆 Grade:</label>
                    <div class="btn-group btn-group-sm d-flex" role="group">
                      <button type="button" class="btn"
                        :class="{ 'btn-primary': showGI, 'btn-outline-primary': !showGI }" @click="showGI = !showGI">
                        <span
                          style="background-color: #3485E3; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">GI</span>
                      </button>
                      <button type="button" class="btn"
                        :class="{ 'btn-primary': showGII, 'btn-outline-primary': !showGII }"
                        @click="showGII = !showGII">
                        <span
                          style="background-color: #F75A86; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">GII</span>
                      </button>
                      <button type="button" class="btn"
                        :class="{ 'btn-primary': showGIII, 'btn-outline-primary': !showGIII }"
                        @click="showGIII = !showGIII">
                        <span
                          style="background-color: #58C471; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">GIII</span>
                      </button>
                      <button type="button" class="btn"
                        :class="{ 'btn-primary': showOP, 'btn-outline-primary': !showOP }" @click="showOP = !showOP">
                        <span
                          style="background-color: #FFA500; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">OP</span>
                      </button>
                      <button type="button" class="btn"
                        :class="{ 'btn-primary': showPREOP, 'btn-outline-primary': !showPREOP }"
                        @click="showPREOP = !showPREOP">
                        <span
                          style="background-color: #9370DB; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">PRE-OP</span>
                      </button>
                    </div>
                  </div>
                  <div class="filter">
                    <label>🌱 Terrain:</label>
                    <div class="btn-group btn-group-sm d-flex" role="group">
                      <button type="button" class="btn"
                        :class="{ 'btn-success': showTurf, 'btn-outline-success': !showTurf }"
                        @click="showTurf = !showTurf">
                        <span
                          style="background-color: #28a745; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">Turf</span>
                      </button>
                      <button type="button" class="btn"
                        :class="{ 'btn-warning': showDirt, 'btn-outline-warning': !showDirt }"
                        @click="showDirt = !showDirt">
                        <span
                          style="background-color: #ffc107; color: black; padding: 2px 4px; border-radius: 3px; font-size: 9px;">Dirt</span>
                      </button>
                    </div>
                  </div>
                  <div class="distance">
                    <label>📏 Distance:</label>
                    <div class="btn-group btn-group-sm d-flex" role="group">
                      <button type="button" class="btn"
                        :class="{ 'btn-info': showSprint, 'btn-outline-info': !showSprint }"
                        @click="showSprint = !showSprint">
                        <span
                          style="background-color: #17a2b8; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">Sprint</span>
                      </button>
                      <button type="button" class="btn" :class="{ 'btn-info': showMile, 'btn-outline-info': !showMile }"
                        @click="showMile = !showMile">
                        <span
                          style="background-color: #17a2b8; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">Mile</span>
                      </button>
                      <button type="button" class="btn"
                        :class="{ 'btn-info': showMedium, 'btn-outline-info': !showMedium }"
                        @click="showMedium = !showMedium">
                        <span
                          style="background-color: #17a2b8; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">Medium</span>
                      </button>
                      <button type="button" class="btn" :class="{ 'btn-info': showLong, 'btn-outline-info': !showLong }"
                        @click="showLong = !showLong">
                        <span
                          style="background-color: #17a2b8; color: white; padding: 2px 4px; border-radius: 3px; font-size: 9px;">Long</span>
                      </button>
                    </div>
                  </div>
                </div>



                <!-- Race Lists -->
                <div class="row">
                  <div class="col-md-4">
                    <div class="card">
                      <div class="card-header">
                        <h6 class="mb-0">Year 1 (Junior Year)</h6>
                      </div>
                      <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        <div class="race-grid">
                          <div v-for="race in filteredRaces_1" :key="race.id" class="race-toggle"
                            :class="{ 'selected': extraRace.includes(race.id) }" @click="toggleRace(race.id)">
                            <div class="race-content">
                              <div class="race-name">{{ race.name }}</div>
                              <div class="race-badges">
                                <span v-if="race.type === 'G3'" class="badge badge-pill"
                                  style="background-color: #58C471;">{{ race.type }}</span>
                                <span v-if="race.type === 'G2'" class="badge badge-pill"
                                  style="background-color: #F75A86;">{{ race.type }}</span>
                                <span v-if="race.type === 'G1'" class="badge badge-pill"
                                  style="background-color: #3485E3;">{{ race.type }}</span>
                                <span v-if="race.type === 'OP'" class="badge badge-pill"
                                  style="background-color: #FFA500;">{{ race.type }}</span>
                                <span v-if="race.type === 'PRE-OP'" class="badge badge-pill"
                                  style="background-color: #9370DB;">{{ race.type }}</span>
                                <span v-if="race.terrain === 'Turf'" class="badge badge-pill"
                                  style="background-color: #28a745; color: white;">{{ race.terrain }}</span>
                                <span v-if="race.terrain === 'Dirt'" class="badge badge-pill"
                                  style="background-color: #ffc107; color: black;">{{ race.terrain }}</span>
                                <span v-if="race.distance === 'Sprint'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Mile'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Medium'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Long'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                              </div>
                              <div class="race-details">{{ race.date }} • {{ race.venue }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div class="card">
                      <div class="card-header">
                        <h6 class="mb-0">Year 2 (Classic Year)</h6>
                      </div>
                      <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        <div class="race-grid">
                          <div v-for="race in filteredRaces_2" :key="race.id" class="race-toggle"
                            :class="{ 'selected': extraRace.includes(race.id) }" @click="toggleRace(race.id)">
                            <div class="race-content">
                              <div class="race-name">{{ race.name }}</div>
                              <div class="race-badges">
                                <span v-if="race.type === 'G3'" class="badge badge-pill"
                                  style="background-color: #58C471;">{{ race.type }}</span>
                                <span v-if="race.type === 'G2'" class="badge badge-pill"
                                  style="background-color: #F75A86;">{{ race.type }}</span>
                                <span v-if="race.type === 'G1'" class="badge badge-pill"
                                  style="background-color: #3485E3;">{{ race.type }}</span>
                                <span v-if="race.type === 'OP'" class="badge badge-pill"
                                  style="background-color: #FFA500;">{{ race.type }}</span>
                                <span v-if="race.type === 'PRE-OP'" class="badge badge-pill"
                                  style="background-color: #9370DB;">{{ race.type }}</span>
                                <span v-if="race.terrain === 'Turf'" class="badge badge-pill"
                                  style="background-color: #28a745; color: white;">{{ race.terrain }}</span>
                                <span v-if="race.terrain === 'Dirt'" class="badge badge-pill"
                                  style="background-color: #ffc107; color: black;">{{ race.terrain }}</span>
                                <span v-if="race.distance === 'Sprint'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Mile'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Medium'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Long'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                              </div>
                              <div class="race-details">{{ race.date }} • {{ race.venue }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="col-md-4">
                    <div class="card">
                      <div class="card-header">
                        <h6 class="mb-0">Year 3 (Senior Year)</h6>
                      </div>
                      <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        <div class="race-grid">
                          <div v-for="race in filteredRaces_3" :key="race.id" class="race-toggle"
                            :class="{ 'selected': extraRace.includes(race.id) }" @click="toggleRace(race.id)">
                            <div class="race-content">
                              <div class="race-name">{{ race.name }}</div>
                              <div class="race-badges">
                                <span v-if="race.type === 'G3'" class="badge badge-pill"
                                  style="background-color: #58C471;">{{ race.type }}</span>
                                <span v-if="race.type === 'G2'" class="badge badge-pill"
                                  style="background-color: #F75A86;">{{ race.type }}</span>
                                <span v-if="race.type === 'G1'" class="badge badge-pill"
                                  style="background-color: #3485E3;">{{ race.type }}</span>
                                <span v-if="race.type === 'OP'" class="badge badge-pill"
                                  style="background-color: #FFA500;">{{ race.type }}</span>
                                <span v-if="race.type === 'PRE-OP'" class="badge badge-pill"
                                  style="background-color: #9370DB;">{{ race.type }}</span>
                                <span v-if="race.terrain === 'Turf'" class="badge badge-pill"
                                  style="background-color: #28a745; color: white;">{{ race.terrain }}</span>
                                <span v-if="race.terrain === 'Dirt'" class="badge badge-pill"
                                  style="background-color: #ffc107; color: black;">{{ race.terrain }}</span>
                                <span v-if="race.distance === 'Sprint'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Mile'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Medium'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                                <span v-if="race.distance === 'Long'" class="badge badge-pill"
                                  style="background-color: #17a2b8; color: white;">{{ race.distance }}</span>
                              </div>
                              <div class="race-details">{{ race.date }} • {{ race.venue }}</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </div>
            <div class="category-card" id="category-skill">
              <div class="category-title">Skill Settings</div>
            <div class="form-group mb-0">
              <div class="row">
                <div class="col">
                  <div class="form-group">
                    <label for="skill-learn">⭐ Skill Learning</label>
                  </div>
                </div>
                <div class="col-auto">
                  <div class="form-group">
                    <div class="skill-notes-alert">
                      <i class="fas fa-info-circle"></i>
                      <span><strong>Notes:</strong> Left Click to Select - Right Click to Blacklist</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Skill Learning Section -->
            <div class="form-group">

              <!-- Priority 0 Section -->
              <div class="priority-section">
                <label class="form-label section-heading">
                  <i class="fas fa-trophy"></i>
                  Priority 0
                </label>
                <div class="selected-skills-box">
                  <div v-if="getSelectedSkillsForPriority(0).length === 0" class="empty-state">
                    The skill that user already select listed in here
                  </div>
                  <div v-else class="selected-skills-list">
                    <div v-for="skillName in getSelectedSkillsForPriority(0)" :key="skillName"
                      class="selected-skill-item">
                      {{ skillName }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Dynamic Priority Sections -->
              <div v-for="priority in getActivePriorities().slice(1)" :key="priority" class="priority-section">
                <label class="form-label section-heading">
                  <i class="fas fa-medal"></i>
                  Priority {{ priority }}
                </label>
                <div class="selected-skills-box">
                  <div v-if="getSelectedSkillsForPriority(priority).length === 0" class="empty-state">
                    The skill that user already select listed in here
                  </div>
                  <div v-else class="selected-skills-list">
                    <div v-for="skillName in getSelectedSkillsForPriority(priority)" :key="skillName"
                      class="selected-skill-item">
                      {{ skillName }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Add/Remove Priority Buttons -->
              <div class="form-group mt-3">
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-outline-primary btn-sm" @click="addPriority">
                    Add Priority
                  </button>
                  <button type="button" class="btn btn-outline-danger btn-sm" @click="removeLastPriority"
                    :disabled="activePriorities.length <= 1">
                    Undo
                  </button>
                </div>
              </div>
            </div>

            <!-- Blacklist Section (inside Skill Settings card) -->
            <div class="form-group">
              <label class="form-label section-heading">
                <i class="fas fa-ban"></i>
                Blacklist
              </label>
              <div class="blacklist-box">
                <div v-if="blacklistedSkills.length === 0" class="empty-state">
                  The skill that user already select blacklisted in here
                </div>
                <div v-else class="blacklisted-skills-list">
                  <div v-for="skillName in blacklistedSkills" :key="skillName" class="blacklisted-skill-item">
                    {{ skillName }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Skill List Section (inside Skill Settings card) -->
            <div class="form-group">
              <div class="skill-list-header" @click="toggleSkillList">
                <div class="skill-list-title">
                  <i class="fas fa-list"></i>
                  Skill List
                </div>
                <div class="skill-list-toggle">
                  <span class="toggle-text">{{ showSkillList ? 'Hide' : 'Show' }}</span>
                  <i class="fas" :class="showSkillList ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                </div>
              </div>
              

              <div v-if="showSkillList" class="skill-list-content">
                <!-- Skill Filter System -->
                <div class="skill-filter-section">
                  <div class="row">
                    <div class="col-md-3">
                      <label class="filter-label">Strategy</label>
                      <select v-model="skillFilter.strategy" class="form-control form-control-sm">
                        <option value="">All Strategies</option>
                        <option v-for="strategy in availableStrategies" :key="strategy" :value="strategy">
                          {{ strategy }}
                        </option>
                      </select>
                    </div>
                    <div class="col-md-3">
                      <label class="filter-label">Distance</label>
                      <select v-model="skillFilter.distance" class="form-control form-control-sm">
                        <option value="">All Distances</option>
                        <option v-for="distance in availableDistances" :key="distance" :value="distance">
                          {{ distance }}
                        </option>
                      </select>
                    </div>
                    <div class="col-md-3">
                      <label class="filter-label">Tier</label>
                      <select v-model="skillFilter.tier" class="form-control form-control-sm">
                        <option value="">All Tiers</option>
                        <option v-for="tier in availableTiers" :key="tier" :value="tier">
                          {{ tier }}
                        </option>
                      </select>
                    </div>
                    <div class="col-md-3">
                      <label class="filter-label">Rarity</label>
                      <select v-model="skillFilter.rarity" class="form-control form-control-sm">
                        <option value="">All Rarities</option>
                        <option v-for="rarity in availableRarities" :key="rarity" :value="rarity">
                          {{ rarity }}
                        </option>
                      </select>
                    </div>
                  </div>
                  <div class="row mt-2">
                    <div class="col-md-8">
                      <label class="filter-label">Search Skill</label>
                      <input v-model.trim="skillFilter.query" type="text" class="form-control form-control-sm" placeholder="Search by skill name or description" />
                    </div>
                    <div class="col-md-4 d-flex align-items-end">
                      <button type="button" class="btn btn-outline-secondary btn-sm ml-auto" @click="clearSkillFilters">
                        <i class="fas fa-times"></i> Clear Filters
                      </button>
                    </div>
                  </div>
                </div>

                <div class="skill-list-container">
                  <div class="skill-type-grid">
                    <div v-for="(skills, skillType) in filteredSkillsByType" :key="skillType" class="skill-type-card">
                      <div class="skill-type-header">
                        <h6 class="skill-type-title">{{ skillType }}</h6>
                        <span class="skill-count">{{ skills.length }} skills</span>
                      </div>
                      <div class="skill-type-content">
                        <div v-for="skill in skills" :key="skill.name" class="skill-item" :class="{
                          'selected': selectedSkills.includes(skill.name),
                          'blacklisted': blacklistedSkills.includes(skill.name)
                        }" @click="toggleSkill(skill.name)" @contextmenu.prevent="toggleBlacklistSkill(skill.name)">
                          <div class="skill-header">
                            <div class="skill-name">{{ skill.name }}</div>
                            <div class="skill-cost">Cost: {{ skill.base_cost }}</div>
                          </div>
                          <div class="skill-details">
                            <div class="skill-type">{{ skill.skill_type }}</div>
                            <div class="skill-description">{{ skill.description }}</div>
                            <div class="skill-tags">
                              <span v-if="skill.strategy" class="skill-tag strategy-tag">{{ skill.strategy }}</span>
                              <span v-if="skill.distance" class="skill-tag distance-tag">{{ skill.distance }}</span>
                              <span v-if="skill.tier" class="skill-tag tier-tag" :data-tier="skill.tier">{{ skill.tier
                              }}</span>
                              <span v-if="skill.rarity" class="skill-tag rarity-tag">{{ skill.rarity }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Skill Learning Settings (inside Skill Settings card) -->
            <div class="form-group toggle-row">
              <div class="row align-items-center">
                <div class="col-md-3">
                  <label class="d-block mb-1">Only learn listed skills</label>
                  <div class="token-toggle" role="group" aria-label="Only learn listed skills">
                    <button type="button" class="token" :class="{ active: learnSkillOnlyUserProvided }" @click="learnSkillOnlyUserProvided = true">Yes</button>
                    <button type="button" class="token" :class="{ active: !learnSkillOnlyUserProvided }" @click="learnSkillOnlyUserProvided = false">No</button>
                  </div>
                </div>
                <div class="col-md-3">
                  <label class="d-block mb-1">Learn before races</label>
                  <div class="token-toggle" :class="{ disabled: true }" role="group" aria-label="Learn before races">
                    <button type="button" class="token" :disabled="true">Yes</button>
                    <button type="button" class="token active" :disabled="true">No</button>
                  </div>
                </div>
                <div class="col-md-3">
                  <div class="form-group">
                    <label for="inputSkillLearnThresholdLimit">Learn when skill points ≥</label>
                    <input v-model="learnSkillThreshold" type="number" class="form-control"
                      id="inputSkillLearnThresholdLimit" placeholder="">
                  </div>
                </div>
                <div class="col-md-3">
                  <label class="d-block mb-1">Manual purchase at end</label>
                  <div class="token-toggle" role="group" aria-label="Manual purchase at end">
                    <button type="button" class="token" :class="{ active: manualPurchase }" @click="manualPurchase = true">On</button>
                    <button type="button" class="token" :class="{ active: !manualPurchase }" @click="manualPurchase = false">Off</button>
                  </div>
                </div>
              </div>
            </div>
            </div>
          </form>
          <!-- <div class="part">
            <br>
                            <h6>Scheduled Settings</h6>
            <hr />
            <div class="row">
              <label for="cronInput" class="col-2 col-form-label">Cron Expression</label>
              <div class="col-10">
                <input v-model="cron"  class="form-control" id="cronInput">
              </div>
            </div>
          </div> -->
        </div>
        <div class="modal-footer d-none"></div>
      </div>
      <!-- Aoharu Cup Configuration Modal -->
      <AoharuConfigModal v-model:show="showAoharuConfigModal" :preliminaryRoundSelections="preliminaryRoundSelections"
        :aoharuTeamNameSelection="aoharuTeamNameSelection" @confirm="handleAoharuConfigConfirm"></AoharuConfigModal>
      <!-- URA Configuration Modal -->
      <UraConfigModal v-model:show="showUraConfigModal" :skillEventWeight="skillEventWeight"
        :resetSkillEventWeightList="resetSkillEventWeightList" @confirm="handleUraConfigConfirm"></UraConfigModal>
      <!-- Support Card Selection Modal -->
      <SupportCardSelectModal v-model:show="showSupportCardSelectModal" @cancel="closeSupportCardSelectModal"
        @confirm="handleSupportCardConfirm"></SupportCardSelectModal>
      <!-- Overlay layer, supports two types of modals -->
      <div v-if="showAoharuConfigModal || showSupportCardSelectModal || showUraConfigModal"
        class="modal-backdrop-overlay" @click.stop></div>
      <!-- Notification -->
      <div class="position-fixed" style="z-index: 5; right: 40%; width: 300px;">
        <div id="liveToast" class="toast hide" role="alert" aria-live="assertive" aria-atomic="true" data-delay="2000">
          <div class="toast-body">
            ✔ Preset saved successfully
          </div>
        </div>
      </div>
      <!-- Weight Warning Notification -->
      <div class="position-fixed" style="z-index: 5; right: 40%; width: 300px;">
        <div id="weightWarningToast" class="toast hide" role="alert" aria-live="assertive" aria-atomic="true"
          data-delay="2000">
          <div class="toast-body" style="color: #856404;">
            ⚠️ <b>All weights in the same year cannot be -1</b>
          </div>
        </div>
      </div>
    </div>
  </div>

              <!-- Custom Character Change Confirmation Modal -->
            <div v-if="showCharacterChangeModal" class="modal fade show character-change-modal" style="display: block; background-color: rgba(0,0,0,0.5);" tabindex="-1">
              <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Character Filter Change</h5>
          <button type="button" class="close" @click="closeCharacterChangeModal">
            <span>&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <p>You have <strong>{{ extraRace.length }}</strong> race(s) selected.</p>
          <div v-if="selectedCharacter">
            <p>Changing to <strong>"{{ selectedCharacter }}"</strong> will:</p>
            <ul>
              <li>Show <strong>{{ getCompatibleRacesCount() }}</strong> compatible race(s)</li>
              <li>Hide <strong>{{ getIncompatibleRacesCount() }}</strong> incompatible race(s)</li>
            </ul>
          </div>
          <div v-else>
            <p>Removing character filter will show all races.</p>
          </div>
          <p>What would you like to do with your current race selections?</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="handleClearSelection">
            <i class="fas fa-trash"></i> Clear Selection
            <small class="d-block">Clear the entire selection</small>
          </button>
          <button type="button" class="btn btn-primary" @click="handleFilterSelection">
            <i class="fas fa-filter"></i> Filter Selection Based on Character Compatibility
            <small class="d-block">Keep the selection but only keep the character compatibility that has already selected</small>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SkillIcon from './SkillIcon.vue';
import AoharuConfigModal from './AoharuConfigModal.vue';
import UraConfigModal from './UraConfigModal.vue';
import SupportCardSelectModal from './SupportCardSelectModal.vue';
import characterData from '../assets/uma_character_data.json';
import raceData from '../assets/uma_race_data.json';
import skillsData from '../assets/umamusume_final_skills_fixed.json';

export default {
  name: "TaskEditModal",
  components: {
    SkillIcon,
    AoharuConfigModal,
    UraConfigModal,
    SupportCardSelectModal
  },
  data: function () {
    return {
      sectionList: [
        { id: 'category-general', label: 'General' },
        { id: 'category-preset', label: 'Preset & Support' },
        { id: 'category-career', label: 'Career' },
        { id: 'category-race', label: 'Race' },
        { id: 'category-skill', label: 'Skills' }
      ],
      activeSection: 'category-general',
      manualPurchase: false,
      showAdvanceOption: false,
      showRaceList: false,
      dataReady: false,
      hideG2: false,
      hideG3: false,
      // Race filtering properties
      raceSearch: '',
      showGI: true,
      showGII: true,
      showGIII: true,
      showOP: true,
      showPREOP: true,
      showTurf: true,
      showDirt: true,
      showSprint: true,
      showMile: true,
      showMedium: true,
      showLong: true,
      // Character filter properties
      selectedCharacter: '',
      characterList: [],
      characterAptitudes: {},
      characterTrainingPeriods: {},
      showCharacterChangeModal: false,
      fujikisekiShowMode: false,
      fujikisekiShowDifficulty: 1,
      levelDataList: [],
      umamusumeTaskTypeList: [
        {
          id: 1,
          name: "Training",
        }
      ],
      umamusumeList: [
        { id: 1, name: 'Special Week' },
        { id: 2, name: 'Silence Suzuka' },
        { id: 3, name: 'Tokai Teio' },
        { id: 4, name: 'Maruzensky' },
        { id: 5, name: 'Oguri Cap' },
        { id: 6, name: 'Taiki Shuttle' },
        { id: 7, name: 'Mejiro Mcqueen' },
        { id: 8, name: 'TM Opera O' },
        { id: 9, name: 'Symboli Rudolf' },
        { id: 10, name: 'Rice Shower' },
        { id: 11, name: 'Gold Ship' },
        { id: 12, name: 'Vodka' },
        { id: 13, name: 'Daiwa Scarlet' },
        { id: 14, name: 'Glass Wonder' },
        { id: 15, name: 'El Condor Pasa' },
        { id: 16, name: 'Air Groove' },
        { id: 17, name: 'Mayano Top Gun' },
        { id: 18, name: 'Super Creek' },
        { id: 19, name: 'Mejiro Ryan' },
        { id: 20, name: 'Agnes Tachyon' },
        { id: 21, name: 'Winning Ticket' },
        { id: 22, name: 'Sakura Bakushin O' },
        { id: 23, name: 'Haru Urara' },
        { id: 24, name: 'Matikanefukukitaru' },
        { id: 25, name: 'Nice Nature' },
        { id: 26, name: 'King Halo' }],
      // Character data from JSON file
      characterList: [],
      // Character training periods from JSON file
      characterTrainingPeriods: {

      },
      // Race data from JSON file
      umamusumeRaceList_1: [],
      umamusumeRaceList_2: [],
      umamusumeRaceList_3: [],
      cultivatePresets: [],
      expectSpeedValue: 650,
      expectStaminaValue: 600,
      expectPowerValue: 650,
      expectWillValue: 300,
      expectIntelligenceValue: 300,

      supportCardLevel: 50,

      presetsUse: {
        name: "Basic Career Preset",
        race_list: [],
        skill: "",
        skill_priority_list: [],
        skill_blacklist: "",
        expect_attribute: [650, 800, 650, 400, 400],
        follow_support_card: { id: 10001, name: 'Beyond This Shining Moment', desc: 'Silence Suzuka' },
        follow_support_card_level: 50,
        clock_use_limit: 99,
        learn_skill_threshold: 9999,
        race_tactic_1: 4,
        race_tactic_2: 4,
        race_tactic_3: 4,
        extraWeight: [],
      },
      // ===  已选择  ===
      selectedExecuteMode: 1,
      expectTimes: 0,
      cron: "* * * * *",

      selectedScenario: 1,
      selectedUmamusumeTaskType: undefined,
      selectedSupportCard: undefined,
      extraRace: [],
      skillLearnPriorityList: [
        {
          priority: 0,
          skills: ""
        }
      ],
      skillPriorityNum: 1,
      skillLearnBlacklist: "",
      learnSkillOnlyUserProvided: false,
      learnSkillBeforeRace: false,
      selectedRaceTactic1: 4,
      selectedRaceTactic2: 4,
      selectedRaceTactic3: 4,
      clockUseLimit: 99,
      learnSkillThreshold: 9999,
      recoverTP: false,
      presetNameEdit: "",
      presetAction: null,
      overwritePresetName: "",
      deletePresetName: "",
      successToast: undefined,
      extraWeight1: [0, 0, 0, 0, 0],
      extraWeight2: [0, 0, 0, 0, 0],
      extraWeight3: [0, 0, 0, 0, 0],

      // Motivation thresholds for trip decisions
      motivationThresholdYear1: 3,
      motivationThresholdYear2: 4,
      motivationThresholdYear3: 4,
      prioritizeRecreation: false,

      // URA配置
      skillEventWeight: [0, 0, 0],
      resetSkillEventWeightList: '',

      // 青春杯配置
      preliminaryRoundSelections: [2, 1, 1, 1],
      aoharuTeamNameSelection: 4,
      showAoharuConfigModal: false,
      showUraConfigModal: false,
      showSupportCardSelectModal: false,

      // Skill data from JSON file
      skillPriority0: [],
      skillPriority1: [],
      skillPriority2: [],
      selectedSkills: [],
      blacklistedSkills: [],
      // Spoiler states for each priority section
      showPriority0: true,
      showPriority1: true,
      showPriority2: true,
      // New properties for dynamic priority system
      activePriorities: [0], // Start with Priority 0
      skillAssignments: {}, // Track which skills are assigned to which priority
      skillFilter: {
        strategy: '',
        distance: '',
        tier: '',
        rarity: '',
        query: ''
      },
      availableStrategies: ['', 'Front Runner', 'Pace Chaser', 'Late Surger', 'End Closer'],
      availableDistances: ['', 'Sprint', 'Mile', 'Medium', 'Long'],
      availableTiers: ['', 'SS', 'S', 'A', 'B', 'C', 'D'],
      availableRarities: ['', 'Unique', 'Rare', 'Normal'],
      showSkillList: false
      ,showPresetMenu: false
    }
  },
  computed: {
    filteredRaces_1() {
      return this.umamusumeRaceList_1.filter(race => {
        const matchesSearch = !this.raceSearch ||
          race.name.toLowerCase().includes(this.raceSearch.toLowerCase()) ||
          race.date.toLowerCase().includes(this.raceSearch.toLowerCase());
        const matchesType =
          (race.type === 'G1' && this.showGI) ||
          (race.type === 'G2' && this.showGII) ||
          (race.type === 'G3' && this.showGIII) ||
          (race.type === 'OP' && this.showOP) ||
          (race.type === 'PRE-OP' && this.showPREOP);
        const matchesTerrain =
          (race.terrain === 'Turf' && this.showTurf) ||
          (race.terrain === 'Dirt' && this.showDirt);
        const matchesDistance =
          (race.distance === 'Sprint' && this.showSprint) ||
          (race.distance === 'Mile' && this.showMile) ||
          (race.distance === 'Medium' && this.showMedium) ||
          (race.distance === 'Long' && this.showLong);

        // Character filter logic
        let matchesCharacter = true;
        if (this.selectedCharacter) {
          const character = this.characterList.find(c => c.name === this.selectedCharacter);
          if (character) {
            // Check if race matches character's aptitude (terrain and distance)
            const matchesCharacterTerrain = race.terrain === character.terrain;

            // Handle multiple distances (e.g., "Medium, Long")
            const characterDistances = character.distance.split(', ').map(d => d.trim());
            const matchesCharacterDistance = characterDistances.includes(race.distance);

            const matchesAptitude = matchesCharacterTerrain && matchesCharacterDistance;

            // Check if race date is within character's training periods
            const characterPeriods = this.characterTrainingPeriods[this.selectedCharacter];
            const matchesTrainingPeriod = characterPeriods && (
              (characterPeriods['Junior Year'] && characterPeriods['Junior Year'].includes(race.date)) ||
              (characterPeriods['Classic Year'] && characterPeriods['Classic Year'].includes(race.date)) ||
              (characterPeriods['Senior Year'] && characterPeriods['Senior Year'].includes(race.date))
            );

            matchesCharacter = matchesAptitude && matchesTrainingPeriod;
          }
        }

        return matchesSearch && matchesType && matchesTerrain && matchesDistance && matchesCharacter;
      });
    },
    filteredRaces_2() {
      return this.umamusumeRaceList_2.filter(race => {
        const matchesSearch = !this.raceSearch ||
          race.name.toLowerCase().includes(this.raceSearch.toLowerCase()) ||
          race.date.toLowerCase().includes(this.raceSearch.toLowerCase());
        const matchesType =
          (race.type === 'G1' && this.showGI) ||
          (race.type === 'G2' && this.showGII) ||
          (race.type === 'G3' && this.showGIII) ||
          (race.type === 'OP' && this.showOP) ||
          (race.type === 'PRE-OP' && this.showPREOP);
        const matchesTerrain =
          (race.terrain === 'Turf' && this.showTurf) ||
          (race.terrain === 'Dirt' && this.showDirt);
        const matchesDistance =
          (race.distance === 'Sprint' && this.showSprint) ||
          (race.distance === 'Mile' && this.showMile) ||
          (race.distance === 'Medium' && this.showMedium) ||
          (race.distance === 'Long' && this.showLong);

        // Character filter logic
        let matchesCharacter = true;
        if (this.selectedCharacter) {
          const character = this.characterList.find(c => c.name === this.selectedCharacter);
          if (character) {
            // Check if race matches character's aptitude (terrain and distance)
            const matchesCharacterTerrain = race.terrain === character.terrain;

            // Handle multiple distances (e.g., "Medium, Long")
            const characterDistances = character.distance.split(', ').map(d => d.trim());
            const matchesCharacterDistance = characterDistances.includes(race.distance);

            const matchesAptitude = matchesCharacterTerrain && matchesCharacterDistance;

            // Check if race date is within character's training periods
            const characterPeriods = this.characterTrainingPeriods[this.selectedCharacter];
            const matchesTrainingPeriod = characterPeriods && (
              (characterPeriods['Junior Year'] && characterPeriods['Junior Year'].includes(race.date)) ||
              (characterPeriods['Classic Year'] && characterPeriods['Classic Year'].includes(race.date)) ||
              (characterPeriods['Senior Year'] && characterPeriods['Senior Year'].includes(race.date))
            );

            matchesCharacter = matchesAptitude && matchesTrainingPeriod;
          }
        }

        return matchesSearch && matchesType && matchesTerrain && matchesDistance && matchesCharacter;
      });
    },
    filteredRaces_3() {
      return this.umamusumeRaceList_3.filter(race => {
        const matchesSearch = !this.raceSearch ||
          race.name.toLowerCase().includes(this.raceSearch.toLowerCase()) ||
          race.date.toLowerCase().includes(this.raceSearch.toLowerCase());
        const matchesType =
          (race.type === 'G1' && this.showGI) ||
          (race.type === 'G2' && this.showGII) ||
          (race.type === 'G3' && this.showGIII) ||
          (race.type === 'OP' && this.showOP) ||
          (race.type === 'PRE-OP' && this.showPREOP);
        const matchesTerrain =
          (race.terrain === 'Turf' && this.showTurf) ||
          (race.terrain === 'Dirt' && this.showDirt);
        const matchesDistance =
          (race.distance === 'Sprint' && this.showSprint) ||
          (race.distance === 'Mile' && this.showMile) ||
          (race.distance === 'Medium' && this.showMedium) ||
          (race.distance === 'Long' && this.showLong);

        // Character filter logic
        let matchesCharacter = true;
        if (this.selectedCharacter) {
          const character = this.characterList.find(c => c.name === this.selectedCharacter);
          if (character) {
            // Check if race matches character's aptitude (terrain and distance)
            const matchesCharacterTerrain = race.terrain === character.terrain;

            // Handle multiple distances (e.g., "Medium, Long")
            const characterDistances = character.distance.split(', ').map(d => d.trim());
            const matchesCharacterDistance = characterDistances.includes(race.distance);

            const matchesAptitude = matchesCharacterTerrain && matchesCharacterDistance;

            // Check if race date is within character's training periods
            const characterPeriods = this.characterTrainingPeriods[this.selectedCharacter];
            const matchesTrainingPeriod = characterPeriods && (
              (characterPeriods['Junior Year'] && characterPeriods['Junior Year'].includes(race.date)) ||
              (characterPeriods['Classic Year'] && characterPeriods['Classic Year'].includes(race.date)) ||
              (characterPeriods['Senior Year'] && characterPeriods['Senior Year'].includes(race.date))
            );

            matchesCharacter = matchesAptitude && matchesTrainingPeriod;
          }
        }

        return matchesSearch && matchesType && matchesTerrain && matchesDistance && matchesCharacter;
      });
    },
    // Group skills by skill_type within each priority
    skillsByTypePriority0() {
      const grouped = {};
      this.skillPriority0.forEach(skill => {
        if (!grouped[skill.skill_type]) {
          grouped[skill.skill_type] = [];
        }
        grouped[skill.skill_type].push(skill);
      });
      return grouped;
    },
    skillsByTypePriority1() {
      const grouped = {};
      this.skillPriority1.forEach(skill => {
        if (!grouped[skill.skill_type]) {
          grouped[skill.skill_type] = [];
        }
        grouped[skill.skill_type].push(skill);
      });
      return grouped;
    },
    skillsByTypePriority2() {
      const grouped = {};
      this.skillPriority2.forEach(skill => {
        if (!grouped[skill.skill_type]) {
          grouped[skill.skill_type] = [];
        }
        grouped[skill.skill_type].push(skill);
      });
      return grouped;
    },
    // New computed property for all skills grouped by type
    allSkillsByType() {
      const allSkills = skillsData;
      const grouped = {};
      allSkills.forEach(skill => {
        if (!grouped[skill.skill_type]) {
          grouped[skill.skill_type] = [];
        }
        grouped[skill.skill_type].push(skill);
      });
      return grouped;
    },
    filteredSkillsByType() {
      const { strategy, distance, tier, rarity, query } = this.skillFilter;
      const allSkills = skillsData;

      // Filter skills based on selected criteria
      const filteredSkills = allSkills.filter(skill => {
        const matchesStrategy = !strategy || (skill.strategy && skill.strategy === strategy);
        const matchesDistance = !distance || (skill.distance && skill.distance === distance);
        const matchesTier = !tier || (skill.tier && skill.tier === tier);
        const matchesRarity = !rarity || (skill.rarity && skill.rarity === rarity);
        const q = (query || '').toLowerCase();
        const matchesQuery = !q ||
          (skill.name && skill.name.toLowerCase().includes(q)) ||
          (skill.description && skill.description.toLowerCase().includes(q));
        return matchesStrategy && matchesDistance && matchesTier && matchesRarity && matchesQuery;
      });

      // Group filtered skills by type
      const grouped = {};
      filteredSkills.forEach(skill => {
        if (!grouped[skill.skill_type]) {
          grouped[skill.skill_type] = [];
        }
        grouped[skill.skill_type].push(skill);
      });

      return grouped;
    }
  },
  mounted() {
    this.loadCharacterData()
    this.loadRaceData()
    this.loadSkillData()
    this.initSelect()
    this.getPresets()
    this.successToast = $('#liveToast').toast({})
    this.$nextTick(() => {
      this.initScrollSpy()
    })
  },
  methods: {
    togglePresetMenu() {
      this.showPresetMenu = !this.showPresetMenu;
    },
    selectPresetAction(which) {
      this.togglePresetAction(which);
      this.showPresetMenu = false;
    },
    loadCharacterData: function () {
      this.characterList = characterData.map(char => ({
        name: char.character_name,
        terrain: char.aptitude.terrain,
        distance: char.aptitude.distance
      }));
      this.characterTrainingPeriods = {};
      characterData.forEach(char => {
        this.characterTrainingPeriods[char.character_name] = {
          'Junior Year': char.objectives.junior_year.dates.map(date => `Junior Year ${date.replace('Junior ', '')}`),
          'Classic Year': char.objectives.classic_year.dates.map(date => `Classic Year ${date.replace('Classic ', '')}`),
          'Senior Year': char.objectives.senior_year.dates.map(date => `Senior Year ${date.replace('Senior ', '')}`)
        };
      });
    },
    loadRaceData: function () {
      // Split races by year based on date
      const juniorRaces = raceData.races.filter(race => race.date.includes('Junior Year'));
      const classicRaces = raceData.races.filter(race => race.date.includes('Classic Year'));
      const seniorRaces = raceData.races.filter(race => race.date.includes('Senior Year'));

      this.umamusumeRaceList_1 = juniorRaces;
      this.umamusumeRaceList_2 = classicRaces;
      this.umamusumeRaceList_3 = seniorRaces;
    },
    loadSkillData: function () {
      // Load all skills from JSON and organize by priority/tier
      const allSkills = skillsData;

      // Organize skills by tier/priority - store full skill objects
      this.skillPriority0 = allSkills.filter(skill => skill.tier === 'SS');
      this.skillPriority1 = allSkills.filter(skill => skill.tier === 'S');
      this.skillPriority2 = allSkills.filter(skill => skill.tier === 'A');
    },
    deleteBox(item, index) {
      if (this.skillLearnPriorityList.length <= 1) {
        return false
      }
      this.skillLearnPriorityList.splice(index, 1)
      this.skillPriorityNum--
      for (let i = index; i < this.skillPriorityNum; i++) {
        this.skillLearnPriorityList[i].priority--
      }
    },
    addBox(item) {
      if (this.skillLearnPriorityList.length >= 5) {
        return false
      }
      this.skillLearnPriorityList.push(
        {
          priority: this.skillPriorityNum++,
          skills: ''
        }
      )
    },
    initSelect: function () {
      this.selectedSupportCard = { id: 10001, name: 'Beyond This Shining Moment', desc: 'Silence Suzuka' }
      this.selectedUmamusumeTaskType = this.umamusumeTaskTypeList[0]
    },
    switchRaceList: function () {
      this.showRaceList = !this.showRaceList
    },
    // Helper: check whether a race matches the currently selected character's aptitude and schedule
    isRaceCompatibleWithSelectedCharacter(race) {
      if (!this.selectedCharacter) return true
      const character = this.characterList.find(c => c.name === this.selectedCharacter)
      if (!character) return true
      // Terrain/distance aptitude
      const matchesTerrain = race.terrain === character.terrain
      const characterDistances = character.distance.split(', ').map(d => d.trim())
      const matchesDistance = characterDistances.includes(race.distance)
      const matchesAptitude = matchesTerrain && matchesDistance
      if (!matchesAptitude) return false
      // Training period (by date label string)
      const periods = this.characterTrainingPeriods[this.selectedCharacter]
      if (!periods) return true
      const inPeriod = (periods['Junior Year'] && periods['Junior Year'].includes(race.date)) ||
                       (periods['Classic Year'] && periods['Classic Year'].includes(race.date)) ||
                       (periods['Senior Year'] && periods['Senior Year'].includes(race.date))
      return !!inPeriod
    },
    // Quick selection methods
    selectAllGI: function () {
      const pool = [
        ...this.umamusumeRaceList_1,
        ...this.umamusumeRaceList_2,
        ...this.umamusumeRaceList_3
      ].filter(race => race.type === 'G1')
       .filter(race => this.isRaceCompatibleWithSelectedCharacter(race))
      pool.forEach(race => { if (!this.extraRace.includes(race.id)) this.extraRace.push(race.id) })
    },
    selectAllGII: function () {
      const pool = [
        ...this.umamusumeRaceList_1,
        ...this.umamusumeRaceList_2,
        ...this.umamusumeRaceList_3
      ].filter(race => race.type === 'G2')
       .filter(race => this.isRaceCompatibleWithSelectedCharacter(race))
      pool.forEach(race => { if (!this.extraRace.includes(race.id)) this.extraRace.push(race.id) })
    },
    selectAllGIII: function () {
      const pool = [
        ...this.umamusumeRaceList_1,
        ...this.umamusumeRaceList_2,
        ...this.umamusumeRaceList_3
      ].filter(race => race.type === 'G3')
       .filter(race => this.isRaceCompatibleWithSelectedCharacter(race))
      pool.forEach(race => { if (!this.extraRace.includes(race.id)) this.extraRace.push(race.id) })
    },
    clearAllRaces: function () {
      this.extraRace = [];
    },
    onCharacterChange: function () {
      // Smart filtering: Show custom confirmation modal when character changes
      if (this.extraRace.length > 0) {
        this.showCharacterChangeModal = true;
      }
    },
    
    getCompatibleRacesCount: function() {
      if (!this.selectedCharacter) return 0;
      
      let count = 0;
      // Count compatible races from all three race lists
      [this.filteredRaces_1, this.filteredRaces_2, this.filteredRaces_3].forEach(races => {
        if (races) count += races.length;
      });
      
      return count;
    },
    
    getIncompatibleRacesCount: function() {
      if (!this.selectedCharacter) return 0;
      
      let totalRaces = 0;
      let compatibleRaces = 0;
      
      // Count total races from all three race lists
      [this.umamusumeRaceList_1, this.umamusumeRaceList_2, this.umamusumeRaceList_3].forEach(races => {
        if (races) totalRaces += races.length;
      });
      
      compatibleRaces = this.getCompatibleRacesCount();
      return totalRaces - compatibleRaces;
    },
    
    // Character change modal methods
    closeCharacterChangeModal: function() {
      this.showCharacterChangeModal = false;
    },
    
    handleClearSelection: function() {
      // Clear the entire selection
      this.extraRace = [];
      this.closeCharacterChangeModal();
    },
    
    handleFilterSelection: function() {
      // Keep the selection but only keep races that are compatible with the selected character
      if (this.selectedCharacter) {
        const character = this.characterList.find(c => c.name === this.selectedCharacter);
        if (character) {
          // Filter races to only keep compatible ones
          this.extraRace = this.extraRace.filter(raceId => {
            // Find the race in any of the three race lists
            let race = null;
            [this.umamusumeRaceList_1, this.umamusumeRaceList_2, this.umamusumeRaceList_3].forEach(raceList => {
              if (!race) {
                race = raceList.find(r => r.id === raceId);
              }
            });
            
            if (!race) return false;
            
            // Check if race matches character's aptitude (terrain and distance)
            const matchesTerrain = race.terrain === character.terrain;
            
            // Handle multiple distances (e.g., "Medium, Long")
            const characterDistances = character.distance.split(', ').map(d => d.trim());
            const matchesDistance = characterDistances.includes(race.distance);
            
            const matchesAptitude = matchesTerrain && matchesDistance;
            
            // Check if race date is within character's training periods
            const characterPeriods = this.characterTrainingPeriods[this.selectedCharacter];
            if (characterPeriods && characterPeriods.length > 0) {
              const raceDate = new Date(race.date);
              const isInTrainingPeriod = characterPeriods.some(period => {
                const startDate = new Date(period.start);
                const endDate = new Date(period.end);
                return raceDate >= startDate && raceDate <= endDate;
              });
              return matchesAptitude && isInTrainingPeriod;
            }
            
            return matchesAptitude;
          });
        }
      }
      this.closeCharacterChangeModal();
    },
    toggleRace: function (raceId) {
      const index = this.extraRace.indexOf(raceId);
      if (index > -1) {
        this.extraRace.splice(index, 1);
      } else {
        this.extraRace.push(raceId);
      }
    },
    toggleSkill: function (skillName) {
      const index = this.selectedSkills.indexOf(skillName);
      if (index > -1) {
        // Remove from selected skills
        this.selectedSkills.splice(index, 1);
        delete this.skillAssignments[skillName];
      } else {
        // Add to selected skills and assign to highest priority
        this.selectedSkills.push(skillName);
        const highestPriority = Math.max(...this.activePriorities);
        this.skillAssignments[skillName] = highestPriority;
      }
    },
    toggleBlacklistSkill: function (skillName) {
      const index = this.blacklistedSkills.indexOf(skillName);
      if (index > -1) {
        this.blacklistedSkills.splice(index, 1);
      } else {
        this.blacklistedSkills.push(skillName);
        // Remove from selected skills if it was selected
        const selectedIndex = this.selectedSkills.indexOf(skillName);
        if (selectedIndex > -1) {
          this.selectedSkills.splice(selectedIndex, 1);
          delete this.skillAssignments[skillName];
        }
      }
    },
    // Spoiler toggle methods
    togglePriority0: function () {
      this.showPriority0 = !this.showPriority0;
    },
    togglePriority1: function () {
      this.showPriority1 = !this.showPriority1;
    },
    togglePriority2: function () {
      this.showPriority2 = !this.showPriority2;
    },
    switchAdvanceOption: function () {
      this.showAdvanceOption = !this.showAdvanceOption
    },
    openUraConfigModal: function () {
      this.showUraConfigModal = true;
    },
    closeUraConfigModal: function () {
      this.showUraConfigModal = false;
    },
    openAoharuConfigModal: function () {
      this.showAoharuConfigModal = true;
    },
    closeAoharuConfigModal: function () {
      this.showAoharuConfigModal = false;
    },
    handleUraConfigConfirm: function (data) {
      this.skillEventWeight = [...data.skillEventWeight];
      this.resetSkillEventWeightList = data.resetSkillEventWeightList;
      this.showUraConfigModal = false;
    },
    handleAoharuConfigConfirm: function (data) {
      this.preliminaryRoundSelections = [...data.preliminaryRoundSelections];
      this.aoharuTeamNameSelection = data.aoharuTeamNameSelection;
      this.showAoharuConfigModal = false;
    },
    cancelTask: function () {
      $('#create-task-list-modal').modal('hide');
    },
    addTask: function () {
      // Convert new skill system to bot-expected format
      var learn_skill_list = []

      // Group selected skills by priority
      const skillsByPriority = {};
      this.selectedSkills.forEach(skillName => {
        const priority = this.skillAssignments[skillName] || 0;
        if (!skillsByPriority[priority]) {
          skillsByPriority[priority] = [];
        }
        skillsByPriority[priority].push(skillName);
      });

      // Convert to bot-expected format (list of lists)
      for (let priority = 0; priority <= Math.max(...this.activePriorities); priority++) {
        if (skillsByPriority[priority] && skillsByPriority[priority].length > 0) {
          learn_skill_list.push(skillsByPriority[priority]);
        } else {
          learn_skill_list.push([]);
        }
      }

      // Convert blacklisted skills to bot-expected format
      var learn_skill_blacklist = [...this.blacklistedSkills];

      console.log(learn_skill_list)
      var ura_reset_skill_event_weight_list = this.resetSkillEventWeightList ? this.resetSkillEventWeightList.split(",").map(item => item.trim()) : []
      let payload = {
        app_name: "umamusume",
        task_execute_mode: this.selectedExecuteMode,
        task_type: this.selectedUmamusumeTaskType.id,
        task_desc: this.selectedUmamusumeTaskType.name,
        attachment_data: {
          "scenario": this.selectedScenario,
          "expect_attribute": [this.expectSpeedValue, this.expectStaminaValue, this.expectPowerValue, this.expectWillValue, this.expectIntelligenceValue],
          "follow_support_card_name": this.selectedSupportCard.name,
          "follow_support_card_level": this.supportCardLevel,
          "extra_race_list": this.extraRace,
          "learn_skill_list": learn_skill_list,
          "learn_skill_blacklist": learn_skill_blacklist,
          "tactic_list": [this.selectedRaceTactic1, this.selectedRaceTactic2, this.selectedRaceTactic3],
          "clock_use_limit": this.clockUseLimit,
          "manual_purchase_at_end": this.manualPurchase,
          "learn_skill_threshold": this.learnSkillThreshold,
          "allow_recover_tp": this.recoverTP,
          "learn_skill_only_user_provided": this.learnSkillOnlyUserProvided,
          "extra_weight": [this.extraWeight1, this.extraWeight2, this.extraWeight3],
          // Motivation thresholds for trip decisions
          "motivation_threshold_year1": this.motivationThresholdYear1,
          "motivation_threshold_year2": this.motivationThresholdYear2,
          "motivation_threshold_year3": this.motivationThresholdYear3,
          "prioritize_recreation": this.prioritizeRecreation,
          // 限时: 富士奇石的表演秀
          "fujikiseki_show_mode": this.fujikisekiShowMode,
          "fujikiseki_show_difficulty": this.fujikisekiShowDifficulty,
          // URA配置
          "ura_config": this.selectedScenario === 1 ? {
            "skillEventWeight": [...this.skillEventWeight],
            "resetSkillEventWeightList": ura_reset_skill_event_weight_list
          } : null,
          // 青春杯配置
          "aoharu_config": this.selectedScenario === 2 ? {
            "preliminaryRoundSelections": [...this.preliminaryRoundSelections],
            "aoharuTeamNameSelection": this.aoharuTeamNameSelection
          } : null
        },
        cron_job_info: {},
      }
      if (this.selectedExecuteMode === 2) {
        payload.cron_job_info = {
          cron: this.cron
        }
      }
      console.log(JSON.stringify(payload))
      this.axios.post("/task", JSON.stringify(payload)).then(
        () => {
          $('#create-task-list-modal').modal('hide');
        }
      )
    },
    applyPresetRace: function () {
      this.selectedScenario = this.presetsUse.scenario || 1
      this.extraRace = this.presetsUse.race_list
      this.expectSpeedValue = this.presetsUse.expect_attribute[0]
      this.expectStaminaValue = this.presetsUse.expect_attribute[1]
      this.expectPowerValue = this.presetsUse.expect_attribute[2]
      this.expectWillValue = this.presetsUse.expect_attribute[3]
      this.expectIntelligenceValue = this.presetsUse.expect_attribute[4]
      this.selectedSupportCard = this.presetsUse.follow_support_card,
        this.supportCardLevel = this.presetsUse.follow_support_card_level,
        this.clockUseLimit = this.presetsUse.clock_use_limit,
        this.learnSkillThreshold = this.presetsUse.learn_skill_threshold,
        this.selectedRaceTactic1 = this.presetsUse.race_tactic_1,
        this.selectedRaceTactic2 = this.presetsUse.race_tactic_2,
        this.selectedRaceTactic3 = this.presetsUse.race_tactic_3,
        this.skillLearnBlacklist = this.presetsUse.skill_blacklist

      // Load motivation thresholds (with defaults)
      this.motivationThresholdYear1 = parseInt(this.presetsUse.motivation_threshold_year1) || 3
      this.motivationThresholdYear2 = parseInt(this.presetsUse.motivation_threshold_year2) || 4
      this.motivationThresholdYear3 = parseInt(this.presetsUse.motivation_threshold_year3) || 4
      this.prioritizeRecreation = this.presetsUse.prioritize_recreation || false

      if ('extraWeight' in this.presetsUse && this.presetsUse.extraWeight != []) {
        this.extraWeight1 = this.presetsUse.extraWeight[0].map(v => Math.max(-1, Math.min(1, v)));
        this.extraWeight2 = this.presetsUse.extraWeight[1].map(v => Math.max(-1, Math.min(1, v)));
        this.extraWeight3 = this.presetsUse.extraWeight[2].map(v => Math.max(-1, Math.min(1, v)));
      }
      else {
        this.extraWeight1 = [0, 0, 0, 0, 0]
        this.extraWeight2 = [0, 0, 0, 0, 0]
        this.extraWeight3 = [0, 0, 0, 0, 0]
      }

      // Load new skill system data if available
      if ('selectedSkills' in this.presetsUse && 'blacklistedSkills' in this.presetsUse && 'skillAssignments' in this.presetsUse && 'activePriorities' in this.presetsUse) {
        // New format - load directly
        this.selectedSkills = [...this.presetsUse.selectedSkills];
        this.blacklistedSkills = [...this.presetsUse.blacklistedSkills];
        this.skillAssignments = { ...this.presetsUse.skillAssignments };
        this.activePriorities = [...this.presetsUse.activePriorities];

        // Also populate old system for UI compatibility
        this.skillLearnBlacklist = this.blacklistedSkills.join(", ");

        // Convert new system back to old format for UI display
        const skillsByPriority = {};
        this.selectedSkills.forEach(skillName => {
          const priority = this.skillAssignments[skillName] || 0;
          if (!skillsByPriority[priority]) {
            skillsByPriority[priority] = [];
          }
          skillsByPriority[priority].push(skillName);
        });

        // Reset old system
        this.skillLearnPriorityList = [{ priority: 0, skills: "" }];
        this.skillPriorityNum = 1;

        // Populate old system from new system
        for (let priority = 0; priority <= Math.max(...this.activePriorities); priority++) {
          if (skillsByPriority[priority] && skillsByPriority[priority].length > 0) {
            if (priority > 0) {
              this.addBox();
            }
            this.skillLearnPriorityList[priority].skills = skillsByPriority[priority].join(", ");
          }
        }
      } else {
        // Old format - convert from skill_priority_list and skill_blacklist
        this.selectedSkills = [];
        this.blacklistedSkills = [];
        this.skillAssignments = {};
        this.activePriorities = [0];

        // Load blacklisted skills
        if (this.presetsUse.skill_blacklist && this.presetsUse.skill_blacklist !== "") {
          this.blacklistedSkills = this.presetsUse.skill_blacklist.split(",").map(skill => skill.trim());
        }

        // Load selected skills from priority list
        if (this.presetsUse.skill_priority_list && this.presetsUse.skill_priority_list.length > 0) {
          this.presetsUse.skill_priority_list.forEach((prioritySkills, priorityIndex) => {
            if (prioritySkills && prioritySkills.length > 0) {
              const skills = prioritySkills[0].split(",").map(skill => skill.trim());
              skills.forEach(skill => {
                if (skill && !this.blacklistedSkills.includes(skill)) {
                  this.selectedSkills.push(skill);
                  this.skillAssignments[skill] = priorityIndex;
                }
              });
              if (priorityIndex > 0) {
                this.activePriorities.push(priorityIndex);
              }
            }
          });
        }
      }

      // Legacy skill loading for backward compatibility
      if ('skill' in this.presetsUse && this.presetsUse.skill != "") {
        this.skillLearnPriorityList[0].skills = this.presetsUse.skill
        while (this.skillPriorityNum > 1) {
          this.deleteBox(0, this.skillPriorityNum - 1)
        }
      }
      else {
        for (let i = 0; i < this.presetsUse.skill_priority_list.length; i++) {
          if (i >= this.skillPriorityNum) {
            this.addBox()
          }
          this.skillLearnPriorityList[i].skills = this.presetsUse.skill_priority_list[i]
        }
        while (this.presetsUse.skill_priority_list.length != 0 &&
          this.skillPriorityNum > this.presetsUse.skill_priority_list.length) {
          this.deleteBox(0, this.skillPriorityNum - 1)
        }
      }

      // 读取青春杯配置（如果存在）
      if ('ura_config' in this.presetsUse) {
        this.skillEventWeight = [...this.presetsUse.ura_config.skillEventWeight];
        this.resetSkillEventWeightList = this.presetsUse.ura_config.resetSkillEventWeightList;
      } else {
        this.skillEventWeight = [0, 0, 0];
        this.resetSkillEventWeightList = '';
      }
      if ('auharuhai_config' in this.presetsUse) {
        this.preliminaryRoundSelections = [...this.presetsUse.auharuhai_config.preliminaryRoundSelections];
        this.aoharuTeamNameSelection = this.presetsUse.auharuhai_config.aoharuTeamNameSelection;
      } else {
        this.preliminaryRoundSelections = [2, 1, 1, 1];
        this.aoharuTeamNameSelection = 4;
      }

    },
    getPresets: function () {
      this.axios.post("/umamusume/get-presets", "").then(
        res => {
          // All presets now come from the server (including starter presets)
          this.cultivatePresets = res.data
        }
      )
    },
    addPresets: function () {
      // Convert new skill system to old format for backward compatibility
      var skill_priority_list = [];
      var skill_blacklist = this.blacklistedSkills.join(", ");

      // Group selected skills by priority
      const skillsByPriority = {};
      this.selectedSkills.forEach(skillName => {
        const priority = this.skillAssignments[skillName] || 0;
        if (!skillsByPriority[priority]) {
          skillsByPriority[priority] = [];
        }
        skillsByPriority[priority].push(skillName);
      });

      // Convert to old format (skill_priority_list)
      for (let priority = 0; priority <= Math.max(...this.activePriorities); priority++) {
        if (skillsByPriority[priority] && skillsByPriority[priority].length > 0) {
          skill_priority_list.push([skillsByPriority[priority].join(", ")]);
        } else {
          skill_priority_list.push([""]);
        }
      }

      let preset = {
        name: this.presetNameEdit,
        scenario: this.selectedScenario,
        race_list: this.extraRace,
        skill_priority_list: skill_priority_list,
        skill_blacklist: skill_blacklist,
        expect_attribute: [this.expectSpeedValue, this.expectStaminaValue, this.expectPowerValue, this.expectWillValue, this.expectIntelligenceValue],
        follow_support_card: this.selectedSupportCard,
        follow_support_card_level: this.supportCardLevel,
        clock_use_limit: this.clockUseLimit,
        learn_skill_threshold: this.learnSkillThreshold,
        race_tactic_1: this.selectedRaceTactic1,
        race_tactic_2: this.selectedRaceTactic2,
        race_tactic_3: this.selectedRaceTactic3,
        extraWeight: [
          this.extraWeight1.map(v => Math.max(-1, Math.min(1, v))),
          this.extraWeight2.map(v => Math.max(-1, Math.min(1, v))),
          this.extraWeight3.map(v => Math.max(-1, Math.min(1, v)))
        ],
        // Motivation thresholds for trip decisions
        motivation_threshold_year1: this.motivationThresholdYear1,
        motivation_threshold_year2: this.motivationThresholdYear2,
        motivation_threshold_year3: this.motivationThresholdYear3,
        prioritize_recreation: this.prioritizeRecreation,
        // New skill system data
        selectedSkills: [...this.selectedSkills],
        blacklistedSkills: [...this.blacklistedSkills],
        skillAssignments: { ...this.skillAssignments },
        activePriorities: [...this.activePriorities]
      }
      // 仅当剧本对应时, 添加URA或青春杯配置
      if (this.selectedScenario === 1) {
        preset.ura_config = {
          skillEventWeight: [...this.skillEventWeight],
          resetSkillEventWeightList: this.resetSkillEventWeightList
        };
      } else if (this.selectedScenario === 2) {
        preset.auharuhai_config = {
          preliminaryRoundSelections: [...this.preliminaryRoundSelections],
          aoharuTeamNameSelection: this.aoharuTeamNameSelection
        };
      }
      let payload = {
        "preset": JSON.stringify(preset)
      }
      console.log(JSON.stringify(payload))
      this.axios.post("/umamusume/add-presets", JSON.stringify(payload)).then(
        () => {
          this.successToast.toast('show')
          this.getPresets()
        }
      )
    },
    togglePresetAction: function (which) {
      this.presetAction = this.presetAction === which ? null : which;
    },
    confirmAddPreset() {
      if (!this.presetNameEdit || this.presetNameEdit.trim() === "") return;
      if (this.presetNameEdit.trim() === 'Default') {
        window.alert('"Default" is reserved. Please choose another name.');
        return;
      }
      const exists = this.cultivatePresets.some(p => p.name === this.presetNameEdit);
      if (exists && !window.confirm(`Preset "${this.presetNameEdit}" exists. Overwrite?`)) {
        return;
      }
      const toastBody = document.querySelector('#liveToast .toast-body');
      if (toastBody) toastBody.textContent = '✔ Preset saved successfully';
      this.addPresets();
      this.presetAction = null;
      this.presetNameEdit = "";
    },
    confirmOverwritePreset() {
      if (!this.overwritePresetName) return;
      // For overwrite we simply save with the same name
      this.presetNameEdit = this.overwritePresetName;
      const toastBody = document.querySelector('#liveToast .toast-body');
      if (toastBody) toastBody.textContent = '✔ Preset overwritten successfully';
      this.addPresets();
      this.presetAction = null;
    },
    confirmDeletePreset() {
      if (!this.deletePresetName) return;
      if (!window.confirm(`Delete preset \"${this.deletePresetName}\"?`)) return;
      const payload = { name: this.deletePresetName };
      this.axios.post("/umamusume/delete-preset", JSON.stringify(payload)).then(() => {
        this.getPresets();
        this.presetAction = null;
        this.deletePresetName = "";
        const toastBody = document.querySelector('#liveToast .toast-body');
        if (toastBody) toastBody.textContent = '✔ Preset deleted successfully';
        this.successToast.toast('show')
      });
    },
    onExtraWeightInput(arr, idx) {
      // 限制输入范围 [-1, 1]
      if (arr[idx] > 1) arr[idx] = 1;
      if (arr[idx] < -1) arr[idx] = -1;
      // 检查是否全为-1，若是则重置最后一个输入为0并弹出警告
      if (arr.filter(v => v === -1).length === arr.length) {
        arr[idx] = 0;
        // 显示警告通知
        this.showWeightWarning();
      }
    },
    showWeightWarning() {
      let warnToast = document.getElementById('weightWarningToast');
      if (warnToast) {
        warnToast.classList.remove('hide');
        warnToast.classList.add('show');
        setTimeout(() => {
          warnToast.classList.remove('show');
          warnToast.classList.add('hide');
        }, 2000);
      }
    },
    openSupportCardSelectModal: function () {
      this.showSupportCardSelectModal = true;
    },
    closeSupportCardSelectModal: function () {
      this.showSupportCardSelectModal = false;
    },
    handleSupportCardConfirm(card) {
      this.selectedSupportCard = card;
      this.showSupportCardSelectModal = false;
    },
    renderSupportCardText(card) {
      if (!card) return '';
      let type = '';
      if (card.id >= 10000 && card.id < 20000) type = 'Speed';
      else if (card.id >= 20000 && card.id < 30000) type = 'Stamina';
      else if (card.id >= 30000 && card.id < 40000) type = 'Power';
      else if (card.id >= 40000 && card.id < 50000) type = 'Guts';
      else if (card.id >= 50000 && card.id < 60000) type = 'Wit';
      if (type) {
        return `【${card.name}】${type}·${card.desc}`;
      } else {
        return `【${card.name}】${card.desc}`;
      }
    },
    // New methods for dynamic priority system
    getActivePriorities: function () {
      return this.activePriorities;
    },
    getSelectedSkillsForPriority: function (priority) {
      return this.selectedSkills.filter(skillName => {
        return this.skillAssignments[skillName] === priority;
      });
    },
    addPriority: function () {
      const maxPriority = Math.max(...this.activePriorities);
      this.activePriorities.push(maxPriority + 1);
    },
    removeLastPriority: function () {
      if (this.activePriorities.length > 1) {
        const removedPriority = this.activePriorities.pop();
        // Move skills from removed priority to the highest remaining priority
        Object.keys(this.skillAssignments).forEach(skillName => {
          if (this.skillAssignments[skillName] === removedPriority) {
            const newHighestPriority = Math.max(...this.activePriorities);
            this.skillAssignments[skillName] = newHighestPriority;
          }
        });
      }
    },
    clearSkillFilters() {
      this.skillFilter = {
        strategy: '',
        distance: '',
        tier: '',
        rarity: '',
        query: ''
      };
    },
    toggleSkillList() {
      this.showSkillList = !this.showSkillList;
    },
    scrollToSection(id) {
      const root = this.$refs.scrollPane;
      const el = root ? root.querySelector(`#${id}`) : document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        this.activeSection = id;
      }
    },
    initScrollSpy() {
      const root = this.$refs.scrollPane;
      if (!root) return;
      this.onScrollSpy = () => {
        const scrollTop = root.scrollTop;
        let current = this.sectionList[0]?.id;
        for (const section of this.sectionList) {
          const el = root.querySelector(`#${section.id}`);
          if (!el) continue;
          const top = el.offsetTop;
          if (top <= scrollTop + 100) {
            current = section.id;
          } else {
            break;
          }
        }
        this.activeSection = current;
      };
      root.addEventListener('scroll', this.onScrollSpy, { passive: true });
      window.addEventListener('resize', this.onScrollSpy, { passive: true });
      // run once
      this.onScrollSpy();
    },
    destroyScrollSpy() {
      const root = this.$refs.contentPane;
      if (root && this.onScrollSpy) root.removeEventListener('scroll', this.onScrollSpy);
      if (this.onScrollSpy) window.removeEventListener('resize', this.onScrollSpy);
    }
  },
  unmounted() {
    this.destroyScrollSpy();
  },
  watch: {

  }
}
</script>

<style scoped>
.btn {
  padding: 0.4rem 0.8rem !important;
  font-size: 1rem !important;
}

.red-button {
  background-color: red !important;
  padding: 0.4rem 0.8rem !important;
  font-size: 1rem !important;
  border-radius: 0.25rem;
}

/* 取消按钮样式 */
.cancel-btn {
  background-color: #dc3545 !important;
  /* Bootstrap的danger红色 */
  color: white !important;
  padding: 0.4rem 0.8rem !important;
  font-size: 1rem !important;
  border-radius: 0.25rem;
  margin-right: 10px;
  /* 与确认按钮间距 */
  border: none;
  cursor: pointer;
}

.cancel-btn:hover {
  background-color: #c82333 !important;
  /* 悬停时更深的红色 */
  color: white !important;
}

/* 确保modal body可以正确滚动 */
.modal-body {
  max-height: 80vh;
  overflow-y: auto;
}

.modal-body--split {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
}

/* Enlarge modal size slightly */
#create-task-list-modal .modal-dialog {
  max-width: 1320px;
  width: 96vw;
}

@media (min-width: 1440px) {
  #create-task-list-modal .modal-dialog {
    max-width: 1380px;
  }
}

.side-nav {
  position: sticky;
  top: 16px;
  height: fit-content;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
}

.side-nav-title {
  font-weight: 700;
  margin-bottom: 8px;
}

.side-nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.side-nav-list li a {
  display: block;
  padding: 8px 10px;
  color: #374151;
  border-radius: 8px;
  text-decoration: none;
}

.side-nav-list li a:hover {
  background: #f3f4f6;
}

.side-nav-list li a.active {
  background: #eef2ff;
  color: #4338ca;
  font-weight: 600;
}

.content-pane {
  min-width: 0;
}

/* 遮罩层样式 - 让TaskEditModal背景变暗并阻止交互 */
.modal-backdrop-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1055;
  /* 确保在TaskEditModal之上，但在AoharuConfigModal之下 */
  pointer-events: auto;
  /* 阻止与背景元素的交互 */
}

/* 只有青春杯配置弹窗时让TaskEditModal变暗 */
#create-task-list-modal.modal.show .modal-content {
  transition: opacity 0.3s ease;
}

#create-task-list-modal.modal.show .modal-content.dimmed {
  opacity: 0.6;
}

/* Smooth scroll behavior for in-pane anchors */
.content-pane {
  scroll-behavior: smooth;
}

.aoharu-btn-bg {
  background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('../assets/img/scenario/aoharu_btn_bg.png') center center no-repeat;
  background-size: cover;
  background-position: center -50px;
  color: #ffffff !important;
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
  font-weight: 600;
  padding: 0.5rem 1rem !important;
  font-size: 1rem !important;
  border-radius: 0.25rem;
  width: 100%;
  min-height: 40px;
  display: inline-block;
  transition: all 0.3s ease;
}

.ura-btn-bg {
  background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('../assets/img/scenario/ura_btn_bg.png') center center no-repeat;
  background-size: cover;
  background-position: center -100px;
  color: #ffffff !important;
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
  font-weight: 600;
  padding: 0.5rem 1rem !important;
  font-size: 1rem !important;
  border-radius: 0.25rem;
  width: 100%;
  min-height: 40px;
  display: inline-block;
  transition: all 0.3s ease;
}

/* Race Toggle Styles */
.race-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding: 8px;
}

/* Category cards (section grouping) */
.category-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}

.category-title {
  font-weight: 700;
  margin-bottom: 12px;
  font-size: 16px;
}

.race-toggle {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.race-toggle:hover {
  background: #e9ecef;
  border-color: #007bff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
}

.race-toggle.selected {
  background: #007bff;
  border-color: #0056b3;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.race-toggle.selected:hover {
  background: #0056b3;
  border-color: #004085;
}

.race-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.race-name {
  font-weight: 600;
  font-size: 14px;
  line-height: 1.3;
  margin-bottom: 4px;
}

.race-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
}

.race-badges .badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 12px;
}

.race-details {
  font-size: 11px;
  opacity: 0.8;
  line-height: 1.2;
}

.race-toggle.selected .race-details {
  opacity: 0.9;
}

/* Skill Toggle Styles */
.skill-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  padding: 8px;
}

.skill-toggle {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.skill-toggle:hover {
  background: #e9ecef;
  border-color: #007bff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
}

.skill-toggle.selected {
  background: #007bff;
  border-color: #0056b3;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.skill-toggle.selected:hover {
  background: #0056b3;
  border-color: #004085;
}

.skill-toggle.blacklist-toggle {
  border-color: #dc3545;
}

.skill-toggle.blacklist-toggle:hover {
  border-color: #c82333;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.15);
}

.skill-toggle.blacklist-toggle.selected {
  background: #dc3545;
  border-color: #c82333;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.skill-toggle.blacklist-toggle.selected:hover {
  background: #c82333;
  border-color: #a71e2a;
}

.skill-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-name {
  font-weight: 600;
  font-size: 12px;
  line-height: 1.2;
  margin-bottom: 2px;
}

.skill-priority {
  font-size: 10px;
  opacity: 0.8;
  line-height: 1.1;
}

.skill-type {
  font-size: 10px;
  opacity: 0.7;
  line-height: 1.1;
  font-style: italic;
}

.skill-description {
  font-size: 9px;
  opacity: 0.8;
  line-height: 1.2;
  margin-top: 4px;
  word-wrap: break-word;
}

.skill-cost {
  font-size: 9px;
  opacity: 0.9;
  line-height: 1.1;
  font-weight: 500;
}

.skill-type-group {
  margin-bottom: 16px;
}

.skill-type-header {
  font-size: 12px;
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: #e9ecef;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.form-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #495057;
}

/* New styles for the redesigned skill learning interface */
.priority-section {
  margin-bottom: 16px;
}

.selected-skills-box,
.blacklist-box {
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  padding: 16px;
  min-height: 80px;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.selected-skills-box:hover,
.blacklist-box:hover {
  border-color: #007bff;
  background: #f0f8ff;
}

.empty-state {
  color: #6c757d;
  font-style: italic;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

.selected-skills-list,
.blacklisted-skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-skill-item,
.blacklisted-skill-item {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.blacklisted-skill-item {
  background: #dc3545;
}

.skill-list-container {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 16px;
  background: white;
  max-height: 500px;
  overflow-y: auto;
}

.skill-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.skill-type-card {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: #f8f9fa;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.skill-type-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.skill-type-header {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-type-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.skill-count {
  font-size: 11px;
  opacity: 0.9;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 12px;
}

.skill-type-content {
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-item {
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 10px;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 11px;
}

.skill-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 6px rgba(0, 123, 255, 0.15);
  transform: translateY(-1px);
}

.skill-item.selected {
  background: linear-gradient(135deg, #007bff, #0056b3);
  border-color: #0056b3;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.skill-item.blacklisted {
  background: linear-gradient(135deg, #dc3545, #c82333);
  border-color: #c82333;
  color: white;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.skill-name {
  font-weight: 600;
  font-size: 12px;
  line-height: 1.2;
}

.skill-cost {
  font-size: 10px;
  opacity: 0.9;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 8px;
}

.skill-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-type {
  font-size: 10px;
  opacity: 0.8;
  line-height: 1.1;
  font-style: italic;
}

.skill-description {
  font-size: 9px;
  opacity: 0.8;
  line-height: 1.3;
  word-wrap: break-word;
}

.skill-item.selected .skill-type,
.skill-item.selected .skill-description {
  opacity: 0.9;
}

.skill-item.blacklisted .skill-type,
.skill-item.blacklisted .skill-description {
  opacity: 0.9;
}

/* Button group styling */
.btn-group {
  display: flex;
  gap: 8px;
}

.btn-group .btn {
  border-radius: 6px;
  font-size: 12px;
  padding: 6px 12px;
}

.btn-group .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.skill-notes-alert {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #6c757d;
}

.skill-notes-alert i {
  margin-right: 5px;
}

.section-heading {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.section-heading i {
  margin-right: 10px;
}

.filter-label {
  font-weight: 600;
  margin-bottom: 5px;
}

.skill-filter-section {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

/* Toggle row switch alignment */
.toggle-row .form-check.form-switch {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-row .form-check-input {
  width: 2.25rem;
  height: 1.125rem;
}

.toggle-row .form-check-label {
  margin-left: 4px;
}

/* Token toggles */
.token-toggle {
  display: inline-flex;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
}

.token-toggle .token {
  background: transparent;
  border: none;
  padding: 6px 14px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
}

.token-toggle .token.active {
  background: #1e40af;
  color: #ffffff;
}

.token-toggle.disabled .token {
  opacity: 0.6;
  cursor: not-allowed;
}

.skill-notes-alert {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #fff3cd, #ffeaa7);
  border: 1px solid #ffc107;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: #856404;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(255, 193, 7, 0.1);
}

.skill-notes-alert i {
  margin-right: 8px;
  color: #ffc107;
}

.section-heading {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #495057;
  padding: 8px 0;
  border-bottom: 2px solid #e9ecef;
}

.section-heading i {
  margin-right: 10px;
  color: #007bff;
}

.filter-label {
  font-weight: 600;
  margin-bottom: 5px;
  color: #495057;
  font-size: 12px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.skill-tag {
  font-size: 8px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.strategy-tag {
  background: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.distance-tag {
  background: #f3e5f5;
  color: #7b1fa2;
  border: 1px solid #e1bee7;
}

.tier-tag {
  background: #fff3e0;
  color: #f57c00;
  border: 1px solid #ffcc02;
}

.tier-tag[data-tier="SS"] {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
  border: 1px solid #c44569;
}

.tier-tag[data-tier="S"] {
  background: linear-gradient(135deg, #ffa726, #ff9800);
  color: white;
  border: 1px solid #f57c00;
}

.tier-tag[data-tier="A"] {
  background: linear-gradient(135deg, #66bb6a, #4caf50);
  color: white;
  border: 1px solid #388e3c;
}

.tier-tag[data-tier="B"] {
  background: linear-gradient(135deg, #42a5f5, #2196f3);
  color: white;
  border: 1px solid #1976d2;
}

.tier-tag[data-tier="C"] {
  background: linear-gradient(135deg, #ab47bc, #9c27b0);
  color: white;
  border: 1px solid #7b1fa2;
}

.tier-tag[data-tier="D"] {
  background: linear-gradient(135deg, #78909c, #607d8b);
  color: white;
  border: 1px solid #455a64;
}

.rarity-tag {
  background: #e8f5e8;
  color: #388e3c;
  border: 1px solid #c8e6c9;
}

.skill-item.selected .skill-tag {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.skill-item.blacklisted .skill-tag {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.skill-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
  margin-bottom: 10px;
}

/* Header action buttons */
.header-actions button.btn.btn-sm.btn-outline-secondary {
  margin-right: 8px;
}

/* Reference palette tweaks */
.btn.auto-btn,
.btn.btn-primary {
  background-color: #1e40af !important;
  border-color: #1e40af !important;
}

.btn.btn-primary:hover,
.btn.auto-btn:hover {
  background-color: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}

.btn-outline-primary {
  color: #1e40af !important;
  border-color: #1e40af !important;
}

.btn-outline-primary:hover {
  background-color: #eef2ff !important;
}

.btn-outline-danger {
  color: #b91c1c !important;
  border-color: #b91c1c !important;
}

.btn-outline-danger:hover {
  background-color: #fee2e2 !important;
}

.btn-outline-success {
  color: #166534 !important;
  border-color: #166534 !important;
}

.btn-outline-success:hover {
  background-color: #dcfce7 !important;
}

.btn.btn-sm {
  padding: 6px 12px !important;
  font-size: 12px !important;
  border-radius: 8px !important;
}

.btn-group .btn {
  border-radius: 8px !important;
}

.dropdown-menu .dropdown-item {
  font-size: 13px;
}

.side-nav-list li a.active {
  background: #eef2ff;
  color: #1e40af;
}

/* Align inline buttons with inputs */
.input-group .btn.btn-sm {
  height: 32px;
  display: inline-flex;
  align-items: center;
}

.preset-actions .preset-save-group {
  display: inline-flex;
  align-items: stretch;
}

.skill-list-header:hover {
  background: linear-gradient(135deg, #0056b3, #004085);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  transform: translateY(-1px);
}

.skill-list-title {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
}

.skill-list-title i {
  margin-right: 10px;
  font-size: 18px;
}

.skill-list-toggle {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 13px;
  transition: all 0.2s ease;
}

.skill-list-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
}

.toggle-text {
  margin-right: 8px;
}

.skill-list-content {
  margin-top: 15px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.advanced-options-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
  margin-bottom: 10px;
}

.advanced-options-header:hover {
  background: linear-gradient(135deg, #0056b3, #004085);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  transform: translateY(-1px);
}

.advanced-options-title {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
}

.advanced-options-title i {
  margin-right: 10px;
  font-size: 18px;
}

.advanced-options-toggle {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 13px;
  transition: all 0.2s ease;
}

.advanced-options-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
}

.advanced-options-content {
  margin-top: 15px;
  animation: fadeIn 0.3s ease;
}

.race-options-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(2, 132, 199, 0.25);
  margin-bottom: 12px;
}

.race-options-header:hover {
  background: linear-gradient(135deg, #0056b3, #004085);
  box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
  transform: translateY(-1px);
}

.race-options-title {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
}

.race-options-title i {
  margin-right: 10px;
  font-size: 18px;
}

.race-options-toggle {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
  font-size: 13px;
  transition: all 0.2s ease;
}

.race-options-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
}

.race-options-content {
  margin-top: 12px;
  animation: fadeIn 0.3s ease;
}

/* Race filter layout tidy */
.race-filters {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 12px;
}

.race-filters .filter {
  grid-column: span 4;
}

.race-filters .quick {
  grid-column: span 4;
}

.race-filters .distance {
  grid-column: span 4;
}

.preset-actions .dropdown-menu {
  display: block;
  position: absolute;
  transform: translateY(8px);
  min-width: 220px;
}

/* Custom Character Change Modal Styles */
.character-change-modal.show {
  z-index: 1050;
}

.character-change-modal .modal-dialog {
  max-width: 500px;
}

.character-change-modal .modal-footer .btn {
  min-width: 200px;
  margin: 5px;
  text-align: left;
  padding: 12px 16px;
}

.character-change-modal .modal-footer .btn small {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 4px;
}

.character-change-modal .modal-footer .btn i {
  margin-right: 8px;
  width: 16px;
}

.character-change-modal .modal-body ul {
  margin-bottom: 0;
}

.character-change-modal .modal-body li {
  margin-bottom: 5px;
}
</style>