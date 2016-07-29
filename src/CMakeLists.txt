cmake_minimum_required(VERSION 3.0)
set( grounder_SRCS
    main.cpp
    grounder.cpp
    VideoGrounder.cpp
    kGrounderView.cpp
)

kconfig_add_kcfg_files(grounder_SRCS settings.kcfgc)
find_package(Qt5Core REQUIRED)
find_package(Qt5Gui REQUIRED)
find_package(Qt5Widgets REQUIRED)
find_package(Qt5Multimedia REQUIRED)

add_executable( grounder ${grounder_SRCS} )

target_link_libraries( grounder
    Qt5::Widgets
    Qt5::MultimediaWidgets
    KF5::CoreAddons
    KF5::WidgetsAddons
    KF5::ConfigCore
    KF5::ConfigGui
    KF5::ConfigWidgets
    KF5::XmlGui
    KF5::I18n
)

install( TARGETS grounder ${INSTALL_TARGETS_DEFAULT_ARGS} )
install( PROGRAMS grounder.desktop  DESTINATION ${XDG_APPS_INSTALL_DIR} )
install( FILES grounderui.rc DESTINATION ${KXMLGUI_INSTALL_DIR}/grounder)
install( FILES grounder.kcfg DESTINATION ${KCFG_INSTALL_DIR})
