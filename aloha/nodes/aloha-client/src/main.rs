use dora_node_api::{
    arrow::array::Float32Array, dora_core::config::DataId, DoraNode, Event, IntoArrow,
};
use eyre::{Context, Result};
use rustypot::{device::xm, DynamixelSerialIO};
use std::{thread::sleep, time::Duration};
use trajectory::{CubicSpline, Trajectory};

fn main() -> Result<()> {
    let (mut node, mut events) = DoraNode::init_from_env()?;
    let mut puppet_left_serial_port = serialport::new("/dev/ttyDXL_puppet_left", 1_000_000)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let mut puppet_right_serial_port = serialport::new("/dev/ttyDXL_puppet_right", 1_000_000)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let io = DynamixelSerialIO::v2();
    xm::sync_write_torque_enable(&io, puppet_left_serial_port.as_mut(), &[7, 8, 9], &[1; 3])
        .expect("Communication error");
    xm::sync_write_torque_enable(
        &io,
        puppet_right_serial_port.as_mut(),
        &[1, 2, 3, 4, 5, 6, 7, 8, 9],
        &[1; 9],
    )
    .expect("Communication error");
    xm::sync_write_operating_mode(&io, puppet_left_serial_port.as_mut(), &[9], &[5])
        .expect("Communication error");
    xm::sync_write_operating_mode(&io, puppet_right_serial_port.as_mut(), &[9], &[5])
        .expect("Communication error");
    xm::sync_write_goal_position(&io, puppet_right_serial_port.as_mut(), &[9], &[3145])
        .expect("Communication error");
    let mut pos_right: Vec<f64> = vec![];

    while let Some(Event::Input {
        id,
        metadata: _,
        data,
    }) = events.recv()
    {
        match id.as_str() {
            "puppet_goal_position" => {
                let buffer: Float32Array = data
                    .to_data()
                    .try_into()
                    .context("Could not parse `puppet_goal_position` as float64")?;
                let target: &[f32] = buffer.values();
                let target = target[..7].iter().map(|&x| x as f64).collect();

                let times = vec![0.0_f64, 0.033];
                let points = vec![pos_right.clone(), target];

                // angular.insert(11, angular[10]);
                // angular.insert(13, angular[12]);

                // let ip = CubicSpline::new(times, points).unwrap();
                // for i in 0..5 {
                //     let t = i as f64 * 0.006_f64;
                //     let p = ip.position(t).unwrap();
                //     let mut angular = p.iter()
                //         .map(|&x| xm::conv::radians_to_pos(x))
                //         .collect::<Vec<_>>();
                //     angular.insert(2, angular[1]);
                //     angular.insert(4, angular[3]);
                //     xm::sync_write_goal_position(
                //         &io,
                //         puppet_right_serial_port.as_mut(),
                //         &[1, 2, 3, 4, 5, 6, 7, 8, 9],
                //         &angular[..9],
                //     )
                //     .expect("Communication error");
                //     sleep(Duration::from_millis(1));
                // }
                // xm::sync_write_goal_position(
                //     &io,
                //     puppet_right_serial_port.as_mut(),
                //     &[1, 2, 3, 4, 5, 6, 7, 8, 9],
                //     &angular[9..18],
                // )
                // .expect("Communication error");
                // xm::sync_write_goal_position(
                //     &io,
                //     puppet_right_serial_port.as_mut(),
                //     &[7, 8, 9],
                //     &angular[15..18],
                // )
                // .expect("Communication error");
            }
            "tick" => {
                let mut pos_left = xm::sync_read_present_position(
                    &io,
                    puppet_left_serial_port.as_mut(),
                    &[1, 2, 4, 6, 7, 8, 9],
                )
                .expect("Communication error");
                let tmp_pos_right = xm::sync_read_present_position(
                    &io,
                    puppet_right_serial_port.as_mut(),
                    &[1, 2, 4, 6, 7, 8, 9],
                )
                .expect("Communication error");
                // pos_left.extend_from_slice(&pos_right);

                pos_right = tmp_pos_right
                    .iter()
                    .map(|&x| xm::conv::pos_to_radians(x))
                    .collect();
                node.send_output(
                    DataId::from("puppet_position".to_owned()),
                    Default::default(),
                    pos_right.clone().into_arrow(),
                )?;
            }
            _ => todo!(),
        };
    }

    Ok(())
}
