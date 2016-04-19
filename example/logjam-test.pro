TEMPLATE = app
CONFIG += console
CONFIG -= app_bundle
CONFIG -= qt

SOURCES += main.c \
    log_test_defs.c \
    logjam_common.c

include(deployment.pri)
qtcAddDeployment()

HEADERS += \
    log_test_defs.h \
    logjam_common.h

