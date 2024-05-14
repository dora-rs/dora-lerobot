use dora_node_api::{dora_core::config::DataId, DoraNode, MetadataParameters};
use eyre::Result;
use rustypot::{device::xl330, DynamixelSerialIO};
use serialport::SerialPort;
use std::{
    sync::mpsc,
    time::{Duration, Instant},
};

static _MAX_MASTER_GRIPER: u32 = 2554;
static _MAX_PUPPET_GRIPER: u32 = 3145;

static _MIN_MASTER_GRIPER: u32 = 1965;
static _MIN_PUPPET_GRIPER: u32 = 2500;
use clap::Parser;

/// Simple aloha teleop program for recording data
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short, long, default_value = "/dev/tty.usbmodem57380045631")]
    master_path: String,

    #[arg(short, long, default_value = "/dev/tty.usbserial-FT8ISNO8")]
    puppet_path: String,

    #[arg(long, default_value = "1000000")]
    master_baudrate: u32,

    #[arg(long, default_value = "1000000")]
    puppet_baudrate: u32,
}

fn main_multithreaded(
    io: DynamixelSerialIO,
    mut master_serial_port: Box<dyn SerialPort>,
    mut puppet_serial_port: Box<dyn SerialPort>,
) -> Result<()> {
    let (tx, rx) = mpsc::channel();
    let (tx_dora, rx_dora) = mpsc::channel();
    std::thread::spawn(move || loop {
        let now = Instant::now();
        let pos =
            xm::sync_read_present_position(&io, master_serial_port.as_mut(), &[1, 2, 3, 4, 6])
                .expect("Communication error");
        tx.send((now, pos)).unwrap();
    });
    let io = DynamixelSerialIO::v2();

    let join = std::thread::spawn(move || {
        while let Ok((_now, pos)) = rx.recv() {
            // Compute linear interpolation for gripper as input and output range missmatch
            // let gripper = (pos[8] - MIN_MASTER_GRIPER) * (MAX_PUPPET_GRIPER - MIN_PUPPET_GRIPER)
            // / (MAX_MASTER_GRIPER - MIN_MASTER_GRIPER)
            // + MIN_PUPPET_GRIPER;
            // let mut target = pos;
            // target[8] = gripper;
            xm::sync_write_goal_position(&io, puppet_serial_port.as_mut(), &[1, 2, 3, 4, 6], &pos)
                .expect("Communication error");
            // println!("elapsed time: {:?}", now.elapsed());
            tx_dora.send(pos).unwrap();
        }
    });

    if std::env::var("DORA_NODE_CONFIG").is_ok() {
        let (mut node, mut _events) = DoraNode::init_from_env()?;
        while let Ok(target) = rx_dora.recv() {
            let output = DataId::from("puppet_goal_position".to_owned());
            let parameters = MetadataParameters::default();
            node.send_output(output.clone(), parameters, target.into_arrow())?;
        }
    };
    join.join().unwrap();
    Ok(())
}

fn main() -> Result<()> {
    let args = Args::parse();
    let master_serial_port = serialport::new(args.master_path, args.master_baudrate)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let mut puppet_serial_port = serialport::new(args.puppet_path, args.puppet_baudrate)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let io = DynamixelSerialIO::v2();
    xm::sync_write_torque_enable(&io, puppet_serial_port.as_mut(), &[1, 2, 3, 4, 6], &[1; 5])
        .expect("Communication error");

    main_multithreaded(io, master_serial_port, puppet_serial_port)?;
    Ok(())
}
