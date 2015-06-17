set( grounder_SRCS
    main.cpp
    grounder.cpp
)

ki18n_wrap_ui(grounder_SRCS grounder.ui)

add_executable( grounder ${grounder_SRCS} )

target_link_libraries( grounder
    Qt5::Widgets
    KF5::CoreAddons
    KF5::I18n
)

install( TARGETS grounder ${INSTALL_TARGETS_DEFAULT_ARGS} )
install( PROGRAMS grounder.desktop  DESTINATION ${XDG_APPS_INSTALL_DIR} )
