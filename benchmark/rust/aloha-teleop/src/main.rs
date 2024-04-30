use eyre::Result;
use rustypot::{device::xm, DynamixelSerialIO};
use serialport::SerialPort;
use std::{sync::mpsc, time::Duration};

static MAX_MASTER_GRIPER: u32 = 2554;
static MAX_PUPPET_GRIPER: u32 = 3145;

static MIN_MASTER_GRIPER: u32 = 1965;
static MIN_PUPPET_GRIPER: u32 = 2500;

fn main_multithreaded(
    io: DynamixelSerialIO,
    mut master_serial_port: Box<dyn SerialPort>,
    mut puppet_serial_port: Box<dyn SerialPort>,
) -> Result<()> {
    let (tx, rx) = mpsc::channel();
    std::thread::spawn(move || loop {
        let pos = xm::sync_read_present_position(
            &io,
            master_serial_port.as_mut(),
            &[1, 2, 3, 4, 5, 6, 7, 8, 9],
        )
        .expect("Communication error");
        tx.send(pos).unwrap();
    });
    let io = DynamixelSerialIO::v2();
    while let Ok(pos) = rx.recv() {
        // Compute linear interpolation for gripper as input and output range missmatch
        let gripper = (pos[8] - MIN_MASTER_GRIPER) * (MAX_PUPPET_GRIPER - MIN_PUPPET_GRIPER)
            / (MAX_MASTER_GRIPER - MIN_MASTER_GRIPER)
            + MIN_PUPPET_GRIPER;
        let mut target = pos;
        target[8] = gripper;
        xm::sync_write_goal_position(
            &io,
            puppet_serial_port.as_mut(),
            &[1, 2, 3, 4, 5, 6, 7, 8, 9],
            &target,
        )
        .expect("Communication error");
    }
    Ok(())
}

fn main() -> Result<()> {
    let master_serial_port = serialport::new("/dev/ttyDXL_master_right", 1_000_000)
        .timeout(Duration::from_millis(200))
        .open()
        .expect("Failed to open port");
    let mut puppet_serial_port = serialport::new("/dev/ttyDXL_puppet_right", 1_000_000)
        .timeout(Duration::from_millis(200))
        .open()
        .expect("Failed to open port");
    let io = DynamixelSerialIO::v2();
    xm::sync_write_torque_enable(
        &io,
        puppet_serial_port.as_mut(),
        &[1, 2, 3, 4, 5, 6, 7, 8, 9],
        &[1; 9],
    )
    .expect("Communication error");

    main_multithreaded(io, master_serial_port, puppet_serial_port)?;
    Ok(())
}
