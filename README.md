### Current State / Problem
Each individual in the group has a contact in Nagios and is included in the notification list for all hosts and services. As our group's responsibilties have expanded, we get a LOT of alerts. No one likes getting woken up at dark-o-clock when they are not on-call, so group members routinely ignore alerts or silence their phones. Habitually ignoring alerts or silencing SMS alerts at night means individuals do not respond to alerts when they are on-call. 

### Solution
Use contact groups in Nagios to manage *who* gets notifed on events and programmatically update the contact group config file based on the on-call rotation. With this approach, individuals will not need to ignore alerts when they are not on-call and alerts when they *are* on-call should be more noticable. 

### Proposed Implementation
There are a few places that the on-call rotation could be stored instead of the current Excel spreadsheet. The group's SharePoint site, a new database table, or the Wiki we just migrated from PAE are some options. Since the SharePoint site will be moved to SPO in the future (thus there's an LOE to make our Nagios process work again), that location seems sub-optimal. Creating a new database table would require someone to create a front-end to view/update the calendar. Since there's already a UI available in Confluence, this seems like the simplest approach. 

### Usage
To update Nagios, I have created `createNagiosOnCallContactGroup.py` which performs the following actions:
1. Create a candidate contact group config file from the on-call schedule 
1. Back up the running contact group config file
1. Copy candidate contact file to the running file
1. Use Nagios to verify the configuration files
1. If candidate configuration verification passes, restart nagios; otherwise restore the backed up file

Before running the script, copy **config.sample** to **config.py** and configure with your settings. 

I propose creating a new Event type for on-call items. Confluence creates a sub-calendar for each event type, so using a dedicated type ensures we are targeting *only* the on-call schedule. All on-call schedule items will be created using this event type. Entries will be made using a fixed format -- a freeform string followed by a delimiter set in config.py `strCalendarTitleDelimiter` and the contact's name which *must* match a contact_name in Nagios. 

To determine the sub-calendar ID associated with the event type, navigate in the wiki to your calendar view. Start [Fiddler](https://www.telerik.com/fiddler) and record traffic, then hide and unhide the event type. Stop recording traffic. Identify a call to Confluence host with URL `/rest/calendar-services/1.0/calendar/preferences/events/hidden.json` and click on it. In the right-hand pane, switch to "Inspectors"/"TextView". The config.py variable strSubCalendarID is set to the sub-calendar ID. 



##### How this all links up:
This script creates a new on-call contact group file to be used in `/usr/local/nagios/etc/objects/Contacts/OnCallSMSContactGroup.cfg` -- this file will need to be included in the nagios.cfg:
~~~~
define contactgroup{
        contactgroup_name       CSGsms
        alias                   CSG SMS Group On-call and Escalation
        members                 e0000001sms, e0000002sms, e0000003sms, e0000004sms
}
~~~~

Members reference contacts file `/usr/local/nagios/etc/objects/Contacts/CSGContactsSMS.cfg`:
~~~~
define contact{
        contact_name                    e0000001sms
        use                             generic-contact
        alias                           Test User1
        host_notifications_enabled      1
        service_notifications_enabled   1
        service_notification_period     24x7
        host_notification_options       d,u,r
        service_notification_options    w,c,r
        pager                           testuser1-sms@example.com
        service_notification_commands   notify-service-by-sms
        host_notification_commands      notify-host-by-sms
}
define contact{
        contact_name                    e0000002sms
        use                             generic-contact
        alias                           Test User2
        host_notifications_enabled      1
        service_notifications_enabled   1
        service_notification_period     24x7
        host_notification_options       d,u,r
        service_notification_options    w,c,r
        pager                           testuser2-sms@example.com
        service_notification_commands   notify-service-by-sms
        host_notification_commands      notify-host-by-sms
}
define contact{
        contact_name                    e0000003sms
        use                             generic-contact
        alias                           Test User3
        host_notifications_enabled      1
        service_notifications_enabled   1
        service_notification_period     24x7
        host_notification_options       d,u,r
        service_notification_options    w,c,r
        pager                           testuser3-sms@example.com
        service_notification_commands   notify-service-by-sms
        host_notification_commands      notify-host-by-sms
}
define contact{
        contact_name                    e0000004sms
        use                             generic-contact
        alias                           Test User4
        host_notifications_enabled      1
        service_notifications_enabled   1
        service_notification_period     24x7
        host_notification_options       d,u,r
        service_notification_options    w,c,r,u
        pager                           testuser4-sms@example.com
        service_notification_commands   notify-service-by-sms
        host_notification_commands      notify-host-by-sms
}
~~~~

Example Host `/usr/local/nagios/etc/objects/Linux/Hosts/SERVER123.cfg` uses prod-linux-host template:
~~~~
define host{
        use             prod-linux-host
        host_name       SERVER123
        alias           SERVER123
        address         SERVER123.example.com
        hostgroups      ds-linux-servers-prod, linuxhosts, ds-customerportal-prod, ds-linux-servers-check-customerportal-prod-ldap
}
~~~~

Uses template `/usr/local/nagios/etc/objects/Templates/Hosts/prod-linux-host.cfg` where CSGsms is the contact_groups:
~~~~
define host{
        name                            prod-linux-host ; The name of this host template
        notifications_enabled           1               ; Host notifications are enabled
        event_handler_enabled           1               ; Host event handler is enabled
        flap_detection_enabled          1               ; Flap detection is enabled
        process_perf_data               1               ; Process performance data
        retain_status_information       1               ; Retain status information across program restarts
        retain_nonstatus_information    1               ; Retain non-status information across program restarts
        check_period                    24x7            ; Check Each Host around the clock
        check_interval                  5               ; Check every 5 minutes
        retry_interval                  1               ; Retry ever 1 minute if fails
        max_check_attempts              5               ; check each host 10 times (max)
        check_command                   check-host-alive; send a single ping to check the host
        notification_period             24x7            ; Send host notifications at any time
        notification_interval           15
        notification_options            d,u,r           ; Notify on down/up/recovery
        contact_groups                  CSGsms          ; Who to notify
        icon_image                      linux40.png
        hostgroups                      linuxhosts, ds-linux-servers-prod
        register                        0               ; DONT REGISTER THIS DEFINITION - ITS NOT A REAL HOST, JUST A TEMPLATE!
}
~~~~


