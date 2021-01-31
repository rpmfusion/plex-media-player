# Use old cmake macro
%global __cmake_in_source_build 1

%global plex_hash 2.58.0.1076-38e019da
%global clients_hash 183-045db5be50e175
%global web_client_desktop 4.29.2-e50e175
%global web_client_tv 4.29.6-045db5b
%global arti_url https://artifacts.plex.tv/web-client-pmp
%global git_url https://github.com/plexinc/plex-media-player

Name:           plex-media-player
Version:        2.58.0
Release:        7%{?dist}
Summary:        Plex Media Player

License:        GPLv2+
URL:            https://plex.tv/
Source0:        %{git_url}/archive/v%{plex_hash}/%{name}-%{plex_hash}.tar.gz
Source1:        plexmediaplayer.desktop
Source2:        plexmediaplayer.appdata.xml
Source3:        plexmediaplayer.service
Source4:        plexmediaplayer.target
Source5:        plexmediaplayer.pkla.disabled
Source6:        plexmediaplayer-standalone
Source7:        plexmediaplayer.te
Source8:        plexmediaplayer.pp
Source9:        plexmediaplayer-standalone-enable

Source90:       %{arti_url}/%{clients_hash}/buildid.cmake#/buildid-%{clients_hash}.cmake
Source91:       %{arti_url}/%{clients_hash}/web-client-desktop-%{web_client_desktop}.tar.xz
Source92:       %{arti_url}/%{clients_hash}/web-client-desktop-%{web_client_desktop}.tar.xz.sha1
Source93:       %{arti_url}/%{clients_hash}/web-client-tv-%{web_client_tv}.tar.xz
Source94:       %{arti_url}/%{clients_hash}/web-client-tv-%{web_client_tv}.tar.xz.sha1

Patch0:         buildfix_qt514.patch
Patch1:         %{git_url}/commit/5430cd807250a8f7329baad76b15a363f35b53fa.patch

# qtwebengine is not available there
ExcludeArch: ppc64le

BuildRequires:  cmake3
BuildRequires:  ninja-build
BuildRequires:  libappstream-glib
BuildRequires:  desktop-file-utils
BuildRequires:  python3
%if 0%{?fedora} > 29
BuildRequires:  systemd-rpm-macros
BuildRequires:  minizip-compat-devel
%else
BuildRequires:  systemd
BuildRequires:  minizip1.2-devel
%endif
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  libGL-devel
%if 0%{?fedora}
BuildRequires:  pkgconfig(libcec)
%endif
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(mpv)
BuildRequires:  pkgconfig(Qt5) >= 5.9.5
BuildRequires:  pkgconfig(Qt5Quick) >= 5.9.5
BuildRequires:  pkgconfig(Qt5WebChannel) >= 5.9.5
BuildRequires:  pkgconfig(Qt5WebEngine) >= 5.9.5
BuildRequires:  pkgconfig(Qt5X11Extras) >= 5.9.5
BuildRequires:  pkgconfig(sdl2)
BuildRequires:  pkgconfig(sm)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xext)
BuildRequires:  pkgconfig(xrandr)
BuildRequires:  pkgconfig(zlib)

# Original copr used that name - kept to ease searching
Obsoletes: plexmediaplayer < 2.40.0
Provides: plexmediaplayer = %{version}-%{release}
Obsoletes: plex < %{version}-%{release}
Provides: plex = %{version}-%{release}

# Needed for qtquick interfaces
Requires: qt5-qtquickcontrols%{_isa} >= 5.9.5

# For xdgscreensaver
Requires: xdg-utils


%description
Plex Media Player - Client for Plex Media Server.

%package session
Summary:        Plex Embedded Client
# User creation.
Requires(pre):  shadow-utils
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description session
This add-on to the %{name} package allows you to start the Plex Media
Player in TV mode at boot for HTPC installations.


%prep
%autosetup -p1 -n %{name}-%{plex_hash}

%build
rm -Rf build
mkdir -p build/dependencies
install -p %{SOURCE90} build/dependencies/buildid-%{clients_hash}.cmake
install -p %{SOURCE91} %{SOURCE92} %{SOURCE93} %{SOURCE94} build/dependencies/


cd build
%cmake3 \
  -GNinja \
  -DOpenGL_GL_PREFERENCE=GLVND \
  -DQTROOT=%{_qt5_prefix} \
  -DMPV_INCLUDE_DIR=%{_includedir}/mpv \
  -DLINUX_DBUS=ON \
  -DLINUX_X11POWER=ON \
  ..

%ninja_build

%install
%ninja_install -C build

mkdir -p %{buildroot}%{_bindir}
install -pm0755 build/src/plexmediaplayer %{buildroot}%{_bindir}/plexmediaplayer
install -pm0755 build/src/pmphelper %{buildroot}%{_bindir}/pmphelper
install -pm0755 %{SOURCE6} %{buildroot}%{_bindir}/plexmediaplayer-standalone

mkdir -p %{buildroot}%{_metainfodir}/
install -pm0644 %{SOURCE2} %{buildroot}%{_metainfodir}/
appstream-util validate-relax --nonet \
  %{buildroot}%{_metainfodir}/plexmediaplayer.appdata.xml

mkdir -p %{buildroot}%{_datadir}/plexmediaplayer/selinux
install -pm0644 %{SOURCE7} %{buildroot}%{_datadir}/plexmediaplayer/selinux/plexmediaplayer.te
install -pm0644 %{SOURCE8} %{buildroot}%{_datadir}/plexmediaplayer/selinux/plexmediaplayer.pp

mkdir -p %{buildroot}%{_datadir}/plexmediaplayer
install -pm0755 %{SOURCE9} \
  %{buildroot}%{_datadir}/plexmediaplayer/plexmediaplayer-standalone-enable

mkdir -p %{buildroot}%{_unitdir}
install -pm0644 %{SOURCE3} %{buildroot}%{_unitdir}/%{name}.service
install -pm0644 %{SOURCE4} %{buildroot}%{_unitdir}/%{name}.target

mkdir -p %{buildroot}%{_sysconfdir}/polkit-1/localauthority/50-local.d
install -pm0644 %{SOURCE5} \
  %{buildroot}%{_sysconfdir}/polkit-1/localauthority/50-local.d/plexmediaplayer.pkla.disabled

desktop-file-install \
  --dir=%{buildroot}%{_datadir}/applications \
  %{SOURCE1}

mkdir -p %{buildroot}%{_sharedstatedir}/plex-media-player

%pre session
# NEVER delete an user or group created by an RPM package. See:
# https://fedoraproject.org/wiki/Packaging:UsersAndGroups#Allocation_Strategies

# Rename plexmediaplayer to plex-media-player
# 
getent group plexmediaplayer >/dev/null && \
   groupmod -n plex-media-player  plexmediaplayer 
getent passwd plexmediaplayer >/dev/null && \
   usermod -m -l plex-media-player \
   -s /sbin/nologin \
   -d %{_sharedstatedir}/plex-media-player \
   -c "Plex Media Player (Standalone)" plexmediaplayer

# Create "plex-media-player" if it not already exists.
#
getent group plex-media-player >/dev/null || groupadd -r plex-media-player  &>/dev/null || :
getent passwd plex-media-player >/dev/null || useradd -r -M \
  -s /sbin/nologin \
  -d %{_sharedstatedir}/plex-media-player \
  -c "Plex Media Player (Standalone)" \
  -G dialout,video,lock,audio \
  -d %{_sharedstatedir}/plex-media-player \
  -g plex-media-player plex-media-player &>/dev/null || :
exit 0

%post session
%systemd_post %{name}.service

%preun session
%systemd_preun %{name}.service

%postun session
%systemd_postun %{name}.service


%files
%license LICENSE
%{_bindir}/plexmediaplayer
%{_bindir}/pmphelper
%{_metainfodir}/plexmediaplayer.appdata.xml
%{_datadir}/applications/plexmediaplayer.desktop
%{_datadir}/icons/hicolor/scalable/apps/plexmediaplayer.svg
%dir %{_datadir}/plexmediaplayer/
%{_datadir}/plexmediaplayer/web-client/*

%files session
%attr(0750,plex-media-player,plex-media-player) %{_sharedstatedir}/plex-media-player
%{_sysconfdir}/polkit-1/localauthority/50-local.d/plexmediaplayer.pkla.disabled
%{_bindir}/plexmediaplayer-standalone
%{_datadir}/plexmediaplayer/plexmediaplayer-standalone-enable
%{_datadir}/plexmediaplayer/selinux/plexmediaplayer.te
%{_datadir}/plexmediaplayer/selinux/plexmediaplayer.pp
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}.target

%changelog
* Sun Jan 31 2021 Leigh Scott <leigh123linux@gmail.com> - 2.58.0-7
- Patch for new mpv

* Mon Nov 23 2020 Leigh Scott <leigh123linux@gmail.com> - 2.58.0-6
- Rebuild for new mpv

* Sat Sep 12 2020 Leigh Scott <leigh123linux@gmail.com> - 2.58.0-5
- Rebuild for libcec

* Tue Aug 18 2020 RPM Fusion Release Engineering <leigh123linux@gmail.com> - 2.58.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 24 2020 Leigh Scott <leigh123linux@gmail.com> - 2.58.0-3
- Use old cmake macro

* Thu Jul 23 2020 Leigh Scott <leigh123linux@gmail.com> - 2.58.0-2
- Improve compatibility with new CMake macro

* Tue May 26 2020 Leigh Scott <leigh123linux@gmail.com> - 2.58.0-1
- Update to 2.58.0

* Thu May 14 2020 Leigh Scott <leigh123linux@gmail.com> - 2.57.0-1
- Update to 2.57.0

* Sat May 02 2020 Leigh Scott <leigh123linux@gmail.com> - 2.56.0-1
- Update to 2.56.0

* Wed Apr 15 2020 Leigh Scott <leigh123linux@gmail.com> - 2.55.0-1
- Update to 2.55.0

* Sun Mar 29 2020 Leigh Scott <leigh123linux@gmail.com> - 2.53.0-1
- Update to 2.53.0

* Mon Mar 09 2020 Leigh Scott <leigh123linux@gmail.com> - 2.52.2-1
- Update to 2.52.2

* Thu Feb 20 2020 Leigh Scott <leigh123linux@gmail.com> - 2.51.0-1
- Update to 2.51.0

* Fri Feb 07 2020 Leigh Scott <leigh123linux@googlemail.com> - 2.50.0-1
- Update to 2.50.0

* Sun Jan 26 2020 Leigh Scott <leigh123linux@googlemail.com> - 2.49.0-1
- Update to 2.49.0

* Sat Jan 11 2020 Leigh Scott <leigh123linux@gmail.com> - 2.48.0-1
- Update to 2.48.0

* Thu Dec 26 2019 Leigh Scott <leigh123linux@googlemail.com> - 2.47.0-1
- Update to 2.47.0

* Fri Nov 08 2019 Leigh Scott <leigh123linux@googlemail.com> - 2.44.0-2
- Fix directory ownership
- Move standalone files to session sub-package
- Use build requires systemd-rpm-macros for fedora
- Remove obsolete scriplets and clean up
- Fix session scriptlets

* Thu Nov 07 2019 Leigh Scott <leigh123linux@gmail.com> - 2.44.0-1
- Update to 2.44.0
- Fix systemd service name
- Fix scriptlet
- Add missing requires qt5-qtquickcontrols

* Wed Nov 06 2019 Leigh Scott <leigh123linux@gmail.com> - 2.40.0-2
- Add lost session sub-package (rfbz#54430)
- Add license
- Use metainfo macros
- Use systemd macros
- Remove obsolete scriptlets for fedora and el8

* Fri Aug 23 2019 Nicolas Chauvet <kwizart@gmail.com> - 2.40.0-1
- Rework spec file
- Bundle web-client-desktop/tv to avoid net access

* Thu May 23 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.34.0-1
- Added a new base background image
- Preview Plex's new PMP experience with many major enhancements including:
  customizable / always accessible sidebar navigation, ability to pin and
  reorder your favorite libraries to the sidebar, quick access to all of your
  media through the "More" menu item, redesigned tab views that remember your
  previous view within each library, acustomizable home screen including pinning
  content rows from any library to home
- Fixed missing news hubs
- Fixed titles missing for music videos in playlist

* Thu May 02 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.33.1-1
- Fixed blurry letter avatar in user menu
- Fixed text getting cut off in related hubs
- Fixed user avatar not appearing in playlists with shared content
- Fixed quick links hubs not correctly positioned with line borders
- Fixed On Right Now hub for Live TV not showing "More..." button
- Fixed loss of focus when only server goes offline

* Thu Apr 18 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.32.0-1
- Fixed user icon in settings modal displaying square instead of round initially

* Tue Apr 02 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.31.0-1
- Added subtitles offset controls for external subtitle files
- Fixed podcasts related episodes getting cut off
- Fixed user ratings showing the wrong value on the extended info screen

* Wed Mar 27 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.30.1-1
- Fixed dashboard not loading when one or more Online Media Sources is disabled

* Mon Mar 25 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.30.0-1
- Desktop web-client updated to 3.83.2
- Fixed playing media when controlled by remote player
- Fixed positioning of poster/text in Live TV conflict items
- Fixed regression with search shortcut
- Fixed issue changing audio or subtitles during playback of multi-part files
- Fixed focus order issue on photo tag page
- Fixed missing Playlists link for Other Videos
- Fixed an issue that prevented playing tracks on playlists with items of
  different sources

* Sat Mar 09 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.29.1-1
- Fixed an issue where search results would come from local machine’s server
  instead of specified server
- Fixed an issue where selecting a search result would open a blank page

* Wed Mar 06 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.29.0-1
- Renamed 'More...' subtitles option to 'Search...'
- Fixed image not loading in actions modal during playback
- Fixed an issue where the wrong images could be displayed for items played
  from other shared or own servers
- Fixed an issue where focus could be lost after reordering types or changing
  types visibility
- Fixed loss of focus on My Webshows/Podcasts when one or more is removed
- Fixed companion pre-play being lost after companion playback
- Fixed an issue where focus could be lost on back navigation
- Fixed regression that caused videos with AC3 audio tracks to direct play and
  result in no sound

* Fri Feb 22 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.28.0-1
- We've updated our tooling to provide an improved user experience
- AAC audio streams are no longer automatically converted to AC3, EAC3, or DTS
  during Direct Stream or Transcode when the related Settings > Audio setting is
  enabled. Instead they will play without conversion
- Fixed loss of focus when going to an empty web shows page
- Fixed navigation order after switching to the admin user
- Fixed News and Podcasts directories so they don't touch navigation bar
- Fixed extended info poster not positioned properly

* Sat Feb 16 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.27.0-1
- Desktop web-client updated to 3.83.1
- Support translation of relative time strings
- Adjusted library page jump bar so more characters can be shown
- Changed user menu from dropdown to full screen modal
- Fixed playback controls not showing the correct duration when
  lightweight seeking
- Fixed possible endless spinner when downloading subtitles
- Fixed player controls sometimes not closing when playing from companion app

* Wed Jan 23 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.26.0-1
- Added actions menu to Web Shows and Podcasts show preplay pages
- Added Chapter Selection title to chapter selection menu
- Don't show "More..." button when there is only one more item
- Fixed possible error on user switcher screen
- Fixed chapter selection sometimes losing focus at the end of the list
- Fixed Live TV restarting from another position when enabling or
  disabling Closed Captioning
- Fixed some issues with video transcoding when it can direct stream

* Fri Jan 11 2019 Jonathan Leroy <jonathan@harrycow.fr> - 2.25.0-1
- Desktop web-client updated to 3.77.4
- Added extended artist biography on artist preplay
- Fixed podcast/web show episodes being marked as played as soon as playback
  is initiated
- Fixed app settings sometimes wrongly showing an item as selected
- Fixed media provider hubs occasionaly not loading
- Fixed an issue where the application could show a blank screen when all
  servers are unavailable

* Tue Dec 18 2018 Jonathan Leroy <jonathan@harrycow.fr> - 2.24.0-1
- Fixed an issue where signing out or switching users could cause the app to
  freeze
- Fixed an issue where the app could crash when loading a type view
- Fixed an issue where focus would be lost after removing the last item from a
  list
- Fixed as issue where enabling recording all episodes for certain shows could
  return in nothing getting added to the priority list
- Fixed an issue that could cause a blank screen to appear after playback
- Fixed loss of focus on episode preplay in some cases

* Mon Dec 03 2018 Jonathan Leroy <jonathan@harrycow.fr> - 2.23.0-1
- Desktop web-client updated to 3.77.2
- Updated look of playlist/collection posters
- Managed users can no longer change the Automatically Sign In setting
- Improved image upscale quality for episode posters
- Fixed sorting/filtering being reset when deleting item

* Mon Nov 26 2018 Jonathan Leroy <jonathan@harrycow.fr> - 2.22.1-1
- Added recording progress to recording schedule
- Subtitles search modal UI changes
- Fixed player control state when playback starts or pauses without
  application control
- Fixed case where focus was lost when navigating back after changing
  list styles
- Fixed play queue starting playback automatically when app is reopened
- Fixed non-functional action buttons on preplay pages in some circumstances
- Fixed case where focus could be lost when navigating into the dashboard
  types header
- Fixed unavailable indicator on preplay pages when media item file
  is unavailable

* Tue Oct 30 2018 Jonathan Leroy <jonathan@harrycow.fr> - 2.21.0-1
- Improvements to subtitles search results titles
- Added new music player UI for podcasts
- Added Related Episodes hub underneath the Podcasts player
- Watch Later and Recommended support has been removed. Please see: 
  plex.tv/blog/subtitles-and-sunsets-big-improvements-little-housekeeping
- Fixed occasional loss of focus on library page when applying “unplayed” filter
- Fixed settings failing to open in some circumstances
- Fixed zip code not disappearing in News settings after selecting a country
  that doesn’t have zip codes
- Fixed selecting a play queue item occasionally not starting playback

* Wed Oct 03 2018 Jonathan Leroy <jonathan@harrycow.fr> - 2.20.0-1
- Desktop web-client updated to 3.71.1
- Improved stream titles (requires PMS 1.13.8 or higher)
- Block app key shortcuts when entering subtitles search title
- Sped up initial loading dashboard
- Fixed blinking thumbnails when moving between items in photo player
- Fixed missing empty dashboard message for managed/shared users with
  restrictions
- Fixed background being lost when navigating away from news player
- Fixed some edge cases around deleting media that could cause the app to become
  unresponsive
- Fixed Chapter Selection focus box not showing sometimes
- Fixed occasional unexpected focused element in app settings modal after
  closing via pointer click
- Fixed some navigation bugs in home screen media types settings
- Fixed settings changes not being immediately visible in the UI
- Fixed pressing seek buttons during music playback making it impossible to
  bring up player controls afterwards
- Fixed subtitles search modal title button width changing when focused
- Fixed news ads playback putting the app in a broken state
- Fixed progress bar being focusable during ads playback
- Fixed news tags and news feed being visible during ads playback
- Fixed news feed being slightly cut off at the bottom
- Fixed issue preventing companion commands
- Fixed display issues with long stream titles on preplay pages

