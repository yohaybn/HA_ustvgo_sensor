
# HA UStvgo sensor
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

## description:
This custom component for watching UStvgo channels via home assistant, broadcasting to google chromecast. 
This component will create senosr for every channel from UStvgo

------------
## instaltion:
Using HACS (add [this repo](https://github.com/yohaybn/HA_ustvgo_sensor ) as custome repository) 

Or copy [ustvgo folder](https://github.com/yohaybn/HA_ustvgo_sensor/tree/main/custom-components/ustvgo ) to your custom component folder and restart your HA.  

add sensor to your configuration.yaml
<pre><code>-  sensor:
	- platform: ustvgo
	  name: ustvgo
	  scan_interval: 3600
</code></pre>
this will create sensor for each channel from UStvgo
## Create Lovelace card
![enter image description here](https://github.com/yohaybn/HA_ustvgo_sensor/blob/main/images/lovelace.png?raw=true)

To create such card that cast the selected channel to selected Chromecast device you need to add the following

**Lovelace card:** (using [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) awesome card )
<pre><code>
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: input_select.media_players
  - type: custom:auto-entities
    card:
      type: glance
      show_name: true
      show_icon: false
      show_state: false
      title: רשימת ערוצים
    filter:
      include:
        - state: ustvgo_*
          options:
            tap_action:
              action: call-service
              service: script.cast_ustvgo
              service_data:
                sensor: this.entity_id
      exclude: []
    sort:
      method: none
    show_empty: true
</code></pre>
**Script:**
<pre><code>
cast_ustvgo:
  sequence:
  - service: media_player.play_media
	data_template:
		media_content_id: >-
			{{ state_attr(sensor, 'm3u') }}
			media_content_type: media
		target:
			entity_id: "{{states('input_select.media_players')}}"
</code></pre>

and create <code>input_select</code> with all your Chromecast devices

## Note
I able to cast to google nest hub and google mini (audio only) but not to LG TV and MiBox 3
## Thanks

to everyone @[Home Assistant](https://www.home-assistant.io/ "Home Assistant")
 for creating the amazing opensource platform for smart home integrations! 🙏🏼 

Thanks to @[benmoose39](https://github.com/benmoose39 "benmoose39") for writing the automation on m3u fetching.
Thanks to @[yishait](https://github.com/yishait "yishait") for the idea.
